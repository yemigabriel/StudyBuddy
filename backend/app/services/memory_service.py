import json
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.config import get_settings

SETTINGS = get_settings()
MEMORY_DIR = Path(SETTINGS.memory_dir)
MAX_SESSION_DOCUMENTS = 5


def _session_path(session_id: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{session_id}.json"


def _memory_backend() -> str:
    return SETTINGS.memory_backend


def _memory_bucket() -> str | None:
    return SETTINGS.memory_bucket


def _memory_key(session_id: str) -> str:
    return f"sessions/{session_id}.json"


def _s3_client():
    return boto3.client("s3")


def _gcs_client():
    return storage.Client()


def _default_state() -> dict:
    return {
        "selected_document": None,
        "documents": [],
        "messages": [],
    }


def _normalize_state(payload: object) -> dict:
    if isinstance(payload, list):
        state = _default_state()
        state["messages"] = payload
        return state

    if isinstance(payload, dict):
        state = _default_state()
        state["selected_document"] = payload.get("selected_document")
        state["documents"] = payload.get("documents", [])
        state["messages"] = payload.get("messages", [])
        return state

    return _default_state()


def get_session_state(session_id: str) -> dict:
    path = _session_path(session_id)
    if path.exists():
        return _normalize_state(json.loads(path.read_text(encoding="utf-8")))

    bucket = _memory_bucket()
    if not bucket:
        return _default_state()

    payload = _download_remote_state(session_id)
    if payload is None:
        return _default_state()

    try:
        path.write_text(payload, encoding="utf-8")
        return _normalize_state(json.loads(payload))
    except json.JSONDecodeError:
        return _default_state()


def get_session_history(session_id: str) -> list[dict[str, str]]:
    return get_session_state(session_id)["messages"]


def get_selected_document(session_id: str) -> str | None:
    return get_session_state(session_id).get("selected_document")


def list_session_documents(session_id: str) -> list[dict[str, str]]:
    return get_session_state(session_id).get("documents", [])


def get_latest_session_document(session_id: str) -> str | None:
    documents = list_session_documents(session_id)
    if not documents:
        return None
    latest = documents[-1]
    return latest.get("document_name")


def set_selected_document(session_id: str, document_name: str | None) -> None:
    state = get_session_state(session_id)
    state["selected_document"] = document_name
    _write_state(session_id, state)


def add_session_document(session_id: str, document_id: str, document_name: str) -> None:
    state = get_session_state(session_id)
    documents = state["documents"]
    if len(documents) >= MAX_SESSION_DOCUMENTS and not any(
        item.get("document_name") == document_name for item in documents
    ):
        raise ValueError(f"Document upload limit reached. You can upload up to {MAX_SESSION_DOCUMENTS} documents.")
    if not any(item.get("document_name") == document_name for item in documents):
        documents.append(
            {
                "document_id": document_id,
                "document_name": document_name,
            }
        )
    _write_state(session_id, state)


def append_conversation(session_id: str, user_message: str, assistant_message: str) -> None:
    state = get_session_state(session_id)
    history = state["messages"]
    timestamp = datetime.now(timezone.utc).isoformat()
    history.extend(
        [
            {"role": "user", "content": user_message, "timestamp": timestamp},
            {
                "role": "assistant",
                "content": assistant_message,
                "timestamp": timestamp,
            },
        ]
    )
    _write_state(session_id, state)


def _write_state(session_id: str, state: dict) -> None:
    path = _session_path(session_id)
    serialized = json.dumps(state, indent=2)
    path.write_text(serialized, encoding="utf-8")
    _upload_remote_state(session_id, path)


def _download_remote_state(session_id: str) -> str | None:
    bucket = _memory_bucket()
    if not bucket:
        return

    backend = _memory_backend()

    if backend == "s3":
        try:
            response = _s3_client().get_object(Bucket=bucket, Key=_memory_key(session_id))
            return response["Body"].read().decode("utf-8")
        except (ClientError, BotoCoreError):
            return None

    if backend == "gcs":
        try:
            blob = _gcs_client().bucket(bucket).blob(_memory_key(session_id))
            if not blob.exists():
                return None
            return blob.download_as_text()
        except GoogleCloudError:
            return None

    return None


def _upload_remote_state(session_id: str, path: Path) -> None:
    bucket = _memory_bucket()
    if not bucket:
        return

    backend = _memory_backend()

    try:
        if backend == "s3":
            _s3_client().upload_file(str(path), bucket, _memory_key(session_id))
            return

        if backend == "gcs":
            blob = _gcs_client().bucket(bucket).blob(_memory_key(session_id))
            blob.upload_from_filename(str(path))
            return
    except (ClientError, BotoCoreError, GoogleCloudError):
        # TODO: add structured logging and retry support for production use.
        return
