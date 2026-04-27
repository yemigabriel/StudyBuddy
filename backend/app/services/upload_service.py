from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> dict[str, int | str]:
    destination = UPLOAD_DIR / f"{uuid4()}-{file.filename}"
    content = await file.read()
    destination.write_bytes(content)

    return {
        "filename": destination.name,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
    }
