import json
import math
import re
from pathlib import Path

INDEX_PATH = Path("data/index.json")
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def ensure_index() -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text("[]", encoding="utf-8")


def read_document_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def embed_text(text: str) -> dict[str, float]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    counts: dict[str, float] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0.0) + 1.0
    return counts


def save_document_chunks(filename: str, text: str) -> int:
    ensure_index()
    chunks = chunk_text(text)
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    filtered_index = [entry for entry in index if entry["filename"] != filename]
    for position, chunk in enumerate(chunks):
        filtered_index.append(
            {
                "filename": filename,
                "chunk_id": position,
                "content": chunk,
                "embedding": embed_text(chunk),
            }
        )

    INDEX_PATH.write_text(json.dumps(filtered_index, indent=2), encoding="utf-8")
    return len(chunks)


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0

    common = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def retrieve_context(query: str, limit: int = 3) -> list[str]:
    ensure_index()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    query_embedding = embed_text(query)

    ranked = sorted(
        index,
        key=lambda entry: cosine_similarity(query_embedding, entry["embedding"]),
        reverse=True,
    )
    return [entry["content"] for entry in ranked[:limit] if entry["content"]]
