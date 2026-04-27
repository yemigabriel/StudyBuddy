from langchain.text_splitter import RecursiveCharacterTextSplitter

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
)


def split_text(text: str) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    chunks = _text_splitter.split_text(normalized)
    return _merge_structural_chunks(chunks)


def _merge_structural_chunks(chunks: list[str]) -> list[str]:
    if not chunks:
        return []

    merged: list[str] = []
    index = 0

    while index < len(chunks):
        chunk = chunks[index].strip()
        if not chunk:
            index += 1
            continue

        if _is_header_like(chunk) and index + 1 < len(chunks):
            combined = f"{chunk}\n\n{chunks[index + 1].strip()}".strip()
            merged.append(combined)
            index += 2
            continue

        if merged and _is_too_short(chunk):
            merged[-1] = f"{merged[-1]}\n\n{chunk}".strip()
            index += 1
            continue

        merged.append(chunk)
        index += 1

    return merged


def _is_header_like(chunk: str) -> bool:
    stripped = chunk.strip()
    words = stripped.replace("#", " ").replace("*", " ").split()
    return stripped.startswith("#") and len(words) <= 12


def _is_too_short(chunk: str) -> bool:
    return len(chunk) < 120 and len(chunk.split()) < 20
