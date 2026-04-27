import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.parsers.document_parser import parse_document
from app.services.chunking_service import split_text
from app.services.memory_service import add_session_document
from app.services.vector_store import get_vector_store

UPLOAD_DIR = Path(get_settings().upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)


async def ingest_upload(file: UploadFile, session_id: str) -> dict[str, int | str]:
    document_id = str(uuid4())
    destination = UPLOAD_DIR / f"{document_id}-{file.filename}"
    logger.info(
        "Starting upload ingest for file=%s session_id=%s document_id=%s",
        file.filename,
        session_id,
        document_id,
    )
    content = await file.read()
    destination.write_bytes(content)
    logger.info("Saved uploaded file to %s (%s bytes).", destination, len(content))

    text = parse_document(str(destination))
    logger.info("Parsed document %s into %s characters of text.", file.filename, len(text))
    chunks = split_text(text)
    parsed_chunk_count = len(chunks)
    logger.info("Split document %s into %s chunk(s).", file.filename, parsed_chunk_count)
    metadatas = [
        {
            "source": destination.name,
            "chunk_index": index,
            "document_id": document_id,
            "document_name": file.filename,
            "session_id": session_id,
        }
        for index, _ in enumerate(chunks)
    ]

    stored_count = 0
    indexing_status = "not_indexed"
    error: str | None = None

    try:
        stored_count = get_vector_store().add_documents(chunks, metadatas=metadatas)
        indexing_status = "indexed"
    except Exception as exc:
        indexing_status = "failed"
        error = str(exc)
        logger.exception(
            "Failed to index uploaded file=%s document_id=%s.",
            file.filename,
            document_id,
        )

    add_session_document(session_id, document_id=document_id, document_name=file.filename)
    logger.info(
        "Finished upload ingest for file=%s parsed_chunks=%s stored_chunks=%s status=%s",
        file.filename,
        parsed_chunk_count,
        stored_count,
        indexing_status,
    )

    return {
        "document_id": document_id,
        "document_name": file.filename,
        "filename": destination.name,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
        "parsed_chunks": parsed_chunk_count,
        "chunks": stored_count,
        "indexing_status": indexing_status,
        "error": error,
    }
