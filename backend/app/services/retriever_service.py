import math
import re
from pathlib import Path

from app.config import get_settings
from app.parsers.document_parser import parse_document
from app.services.chunking_service import split_text
from app.services.embedding_service import embed_text
from app.services.vector_store import SearchResult, get_vector_store


def retrieve_context(
    retrieval_query: str,
    document_name: str | None = None,
    initial_k: int = 10,
    final_k: int = 5,
    max_chars: int = 2500,
) -> list[str]:
    try:
        store = get_vector_store()

        initial_results = store.query(
            retrieval_query,
            k=initial_k,
            document_name=document_name,
        )

        ranked = rerank_results(retrieval_query, merge_results(initial_results))
        selected = [result.document for result in ranked[:final_k] if result.document]
        if selected:
            return trim_context(selected, max_chars=max_chars)
    except Exception:
        pass

    try:
        fallback_chunks = retrieve_from_source_document(
            retrieval_query,
            document_name=document_name,
            final_k=final_k,
            max_chars=max_chars,
        )
        return fallback_chunks
    except Exception:
        return []


def merge_results(*result_sets: list[SearchResult]) -> list[SearchResult]:
    merged: dict[str, SearchResult] = {}
    text_keys: dict[str, str] = {}
    for result_set in result_sets:
        for result in result_set:
            text_key = normalize_chunk_text(result.document)
            existing_id = text_keys.get(text_key)
            candidate_id = existing_id or result.id
            current = merged.get(candidate_id)
            if current is None or result.score > current.score:
                merged[candidate_id] = result
                text_keys[text_key] = candidate_id
    return list(merged.values())


def rerank_results(question: str, results: list[SearchResult]) -> list[SearchResult]:
    if not results:
        return []

    query_embedding = embed_text(question)
    query_terms = set(tokenize(question))
    overview_query = is_document_overview_query(question)
    rescored: list[SearchResult] = []

    for result in results:
        doc_embedding = embed_text(result.document)
        semantic_score = cosine_similarity(query_embedding, doc_embedding)
        overlap_score = keyword_overlap(query_terms, set(tokenize(result.document)))
        structure_score = score_chunk_structure(
            result.document,
            result.metadata,
            overview_query=overview_query,
        )
        intent_score = score_chunk_for_query_intent(result.document, question)
        final_score = (
            (semantic_score * 0.6)
            + (overlap_score * 0.15)
            + structure_score
            + intent_score
        )
        rescored.append(
            SearchResult(
                id=result.id,
                document=result.document,
                metadata=result.metadata,
                score=final_score,
            )
        )

    return sorted(rescored, key=lambda item: item.score, reverse=True)


def trim_context(chunks: list[str], max_chars: int) -> list[str]:
    total = 0
    selected: list[str] = []
    for chunk in chunks:
        if total >= max_chars:
            break
        remaining = max_chars - total
        clipped = chunk[:remaining]
        selected.append(clipped)
        total += len(clipped)
    return selected


def build_context(chunks: list[str], max_chars: int = 2500) -> str:
    trimmed = trim_context(chunks, max_chars=max_chars)
    return "\n\n".join(trimmed)


def keyword_overlap(query_terms: set[str], doc_terms: set[str]) -> float:
    if not query_terms or not doc_terms:
        return 0.0
    overlap = len(query_terms & doc_terms)
    return overlap / max(len(query_terms), 1)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0

    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def retrieve_from_source_document(
    question: str,
    document_name: str | None,
    final_k: int,
    max_chars: int,
) -> list[str]:
    if not document_name:
        return []

    path = find_uploaded_document(document_name)
    if path is None:
        return []

    chunks = split_text(parse_document(str(path)))
    if not chunks:
        return []

    overview_query = is_document_overview_query(question)
    selected = select_fallback_chunks(
        chunks,
        question,
        final_k=final_k,
        overview_query=overview_query,
    )
    return trim_context(selected, max_chars=max_chars)


def find_uploaded_document(document_name: str) -> Path | None:
    upload_dir = Path(get_settings().upload_dir)
    matches = sorted(upload_dir.glob(f"*-{document_name}"))
    return matches[-1] if matches else None


def select_fallback_chunks(
    chunks: list[str],
    question: str,
    final_k: int,
    overview_query: bool,
) -> list[str]:
    filtered = [chunk for chunk in chunks if not is_low_value_chunk(chunk, overview_query)]
    if not filtered:
        filtered = chunks

    if overview_query:
        scored = []
        for index, chunk in enumerate(filtered):
            score = 0.0
            normalized = chunk.lower()
            if "abstract" in normalized:
                score += 1.0
            if "introduction" in normalized:
                score += 0.7
            if any(term in normalized for term in ("objective", "objectives", "aim", "purpose")):
                score += 0.8
            if any(term in normalized for term in ("this study", "this paper", "presents", "proposed", "framework")):
                score += 0.5
            score += max(0, 0.2 - (index * 0.01))
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:final_k]]

    query_terms = set(tokenize(question))
    scored = []
    for index, chunk in enumerate(filtered):
        overlap = keyword_overlap(query_terms, set(tokenize(chunk)))
        score = overlap + max(0, 0.05 - (index * 0.002))
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:final_k]]


def is_low_value_chunk(chunk: str, overview_query: bool) -> bool:
    normalized = chunk.lower().strip()
    word_count = len(tokenize(chunk))

    if normalized.startswith("#") and word_count <= 14:
        return True

    if overview_query and any(
        term in normalized
        for term in ("references", "bibliography", "limitations", "future directions")
    ):
        return True

    return False


def normalize_chunk_text(text: str) -> str:
    return " ".join(text.lower().split())


def is_document_overview_query(question: str) -> bool:
    normalized = question.lower()
    patterns = (
        "what is this document",
        "what's this document",
        "what is this file",
        "what does this document say",
        "what is it about",
        "summarize this document",
        "document about",
        "objective",
        "objectives",
        "aim",
        "purpose",
    )
    return any(pattern in normalized for pattern in patterns)


def score_chunk_structure(
    chunk: str,
    metadata: dict,
    overview_query: bool,
) -> float:
    normalized = chunk.lower().strip()
    word_count = len(tokenize(chunk))
    score = 0.0

    if normalized.startswith("#") and word_count <= 14:
        score -= 0.45
    elif word_count > 40:
        score += 0.12

    if len(chunk) > 250 and any(punct in chunk for punct in ".:;"):
        score += 0.08

    if overview_query:
        chunk_index = metadata.get("chunk_index")
        if isinstance(chunk_index, int):
            if chunk_index <= 3:
                score += 0.2
            elif chunk_index >= 40:
                score -= 0.08

        if "abstract" in normalized:
            score += 0.35
        if "introduction" in normalized:
            score += 0.18
        if any(term in normalized for term in ("references", "bibliography", "limitations", "future directions")):
            score -= 0.3

    return score


def score_chunk_for_query_intent(chunk: str, question: str) -> float:
    normalized_chunk = chunk.lower()
    normalized_question = question.lower()
    score = 0.0

    if any(term in normalized_question for term in ("objective", "objectives", "aim", "purpose")):
        if any(term in normalized_chunk for term in ("objective", "objectives", "aim", "purpose", "this study", "this paper", "presents", "proposed")):
            score += 0.22

    if is_document_overview_query(question):
        if any(term in normalized_chunk for term in ("this study", "this paper", "we propose", "presents", "overall", "framework")):
            score += 0.18

    return score


AMBIGUOUS_PHRASES = (
    "this document",
    "that document",
    "this file",
    "that file",
    "what does it say",
    "what is it about",
    "what is this about",
    "explain this",
    "explain it",
    "summarize it",
    "tell me more about it",
)


def is_ambiguous_query(query: str) -> bool:
    normalized = query.strip().lower()
    if normalized in {"this", "it"}:
        return True
    if any(phrase in normalized for phrase in AMBIGUOUS_PHRASES):
        return True
    if len(normalized.split()) <= 6 and re.search(r"\b(this|it)\b", normalized):
        return True
    return bool(re.fullmatch(r"(what|explain|summarize)\s+(this|it)\??", normalized))
