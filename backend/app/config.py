import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _is_lambda_runtime() -> bool:
    return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))


def _is_cloud_run_runtime() -> bool:
    return bool(os.getenv("K_SERVICE"))


def _default_runtime_data_root() -> Path:
    if _is_lambda_runtime() or _is_cloud_run_runtime():
        return Path("/tmp/studybuddy")
    return Path("data")


def _default_memory_root() -> Path:
    if _is_lambda_runtime() or _is_cloud_run_runtime():
        return Path("/tmp/studybuddy/memory/sessions")
    return Path("../memory/sessions")


def _default_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS")
    if not raw or not raw.strip():
        logger.warning("CORS_ALLOW_ORIGINS is not set! Defaulting safely to local development origin.")
        return ["http://localhost:3000"]
    
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    vector_db: str
    pinecone_api_key: str | None
    pinecone_index_name: str | None
    memory_backend: str
    memory_bucket: str | None
    chroma_path: str
    chroma_collection_name: str
    embedding_model: str
    chat_model: str
    upload_dir: str
    memory_dir: str
    cors_allow_origins: list[str]


def get_settings() -> Settings:
    runtime_root = _default_runtime_data_root()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        vector_db=os.getenv("VECTOR_DB", "chroma").strip().lower(),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME"),
        memory_backend=os.getenv("MEMORY_BACKEND", "local").strip().lower(),
        memory_bucket=os.getenv("STUDYBUDDY_MEMORY_BUCKET"),
        chroma_path=os.getenv("CHROMA_PATH", str(runtime_root / "chroma")),
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "studybuddy_chunks"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        upload_dir=os.getenv("UPLOAD_DIR", str(runtime_root / "uploads")),
        memory_dir=os.getenv("MEMORY_DIR", str(_default_memory_root())),
        cors_allow_origins=_default_cors_origins(),
    )
