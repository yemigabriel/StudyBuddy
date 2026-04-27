from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.services.rag_service import read_document_text, save_document_chunks

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def ingest_upload(file: UploadFile) -> dict[str, int | str]:
    destination = UPLOAD_DIR / f"{uuid4()}-{file.filename}"
    content = await file.read()
    destination.write_bytes(content)
    text = read_document_text(file.filename, content)
    chunks = save_document_chunks(destination.name, text)

    return {
        "filename": destination.name,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
        "chunks": chunks,
    }
