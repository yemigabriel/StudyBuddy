from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalResult:
    name: str
    category: str
    passed: bool
    score: float
    details: str


@dataclass(frozen=True)
class RetrievalMetrics:
    precision: float
    recall: float
    hit_rate: float
    mrr: float
    relevant_retrieved: int
    retrieved_count: int
    matched_fragments: int
    total_fragments: int
    first_relevant_rank: int | None


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def contains_all(text: str, expected_fragments: list[str]) -> tuple[bool, list[str]]:
    normalized_text = normalize_text(text)
    missing = [
        fragment for fragment in expected_fragments
        if normalize_text(fragment) not in normalized_text
    ]
    return not missing, missing


def contains_any(text: str, fragments: list[str]) -> tuple[bool, list[str]]:
    normalized_text = normalize_text(text)
    found = [
        fragment for fragment in fragments
        if normalize_text(fragment) in normalized_text
    ]
    return bool(found), found


def score_retrieval(
    case_name: str,
    retrieved_chunks: list[str],
    expected_fragments: list[str],
) -> EvalResult:
    joined = "\n".join(retrieved_chunks)
    passed, missing = contains_all(joined, expected_fragments)
    score = 1.0 if passed else 0.0
    details = "all expected evidence retrieved" if passed else f"missing evidence: {', '.join(missing)}"
    return EvalResult(
        name=case_name,
        category="retrieval",
        passed=passed,
        score=score,
        details=details,
    )


def calculate_retrieval_metrics(
    retrieved_chunks: list[str],
    expected_fragments: list[str],
) -> RetrievalMetrics:
    normalized_fragments = [normalize_text(fragment) for fragment in expected_fragments]
    matched_fragments: set[str] = set()
    relevant_retrieved = 0
    first_relevant_rank: int | None = None

    for index, chunk in enumerate(retrieved_chunks, start=1):
        normalized_chunk = normalize_text(chunk)
        chunk_matches = [
            fragment for fragment in normalized_fragments
            if fragment in normalized_chunk
        ]
        if chunk_matches:
            relevant_retrieved += 1
            matched_fragments.update(chunk_matches)
            if first_relevant_rank is None:
                first_relevant_rank = index

    retrieved_count = len(retrieved_chunks)
    total_fragments = len(normalized_fragments)
    matched_count = len(matched_fragments)

    precision = (
        relevant_retrieved / retrieved_count
        if retrieved_count > 0
        else 0.0
    )
    recall = (
        matched_count / total_fragments
        if total_fragments > 0
        else 0.0
    )
    hit_rate = 1.0 if relevant_retrieved > 0 else 0.0
    mrr = (1.0 / first_relevant_rank) if first_relevant_rank else 0.0

    return RetrievalMetrics(
        precision=precision,
        recall=recall,
        hit_rate=hit_rate,
        mrr=mrr,
        relevant_retrieved=relevant_retrieved,
        retrieved_count=retrieved_count,
        matched_fragments=matched_count,
        total_fragments=total_fragments,
        first_relevant_rank=first_relevant_rank,
    )


def score_answer(
    case_name: str,
    answer: str,
    expected_fragments: list[str],
    forbidden_fragments: list[str],
) -> EvalResult:
    has_expected, missing = contains_all(answer, expected_fragments)
    has_forbidden, found_forbidden = contains_any(answer, forbidden_fragments)
    passed = has_expected and not has_forbidden
    score = 1.0 if passed else 0.0

    detail_parts: list[str] = []
    if missing:
        detail_parts.append(f"missing answer evidence: {', '.join(missing)}")
    if found_forbidden:
        detail_parts.append(f"forbidden content present: {', '.join(found_forbidden)}")
    if not detail_parts:
        detail_parts.append("answer satisfied expected checks")

    return EvalResult(
        name=case_name,
        category="answer",
        passed=passed,
        score=score,
        details="; ".join(detail_parts),
    )
