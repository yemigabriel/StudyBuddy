import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

MEMORY_DIR = Path("../memory/sessions")


def _session_path(session_id: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{session_id}.json"


def _s3_bucket() -> str | None:
    return os.getenv("STUDYBUDDY_MEMORY_BUCKET")


def _s3_key(session_id: str) -> str:
    return f"sessions/{session_id}.json"


def _client():
    return boto3.client("s3")


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

    bucket = _s3_bucket()
    if not bucket:
        return _default_state()

    try:
        response = _client().get_object(Bucket=bucket, Key=_s3_key(session_id))
        payload = response["Body"].read().decode("utf-8")
        path.write_text(payload, encoding="utf-8")
        return _normalize_state(json.loads(payload))
    except (ClientError, BotoCoreError, json.JSONDecodeError):
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
    _upload_to_s3(session_id, path)


def _upload_to_s3(session_id: str, path: Path) -> None:
    bucket = _s3_bucket()
    if not bucket:
        return

    try:
        _client().upload_file(str(path), bucket, _s3_key(session_id))
    except (ClientError, BotoCoreError):
        # TODO: add structured logging and retry support for production use.
        return
