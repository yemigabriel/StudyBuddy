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


def get_session_history(session_id: str) -> list[dict[str, str]]:
    path = _session_path(session_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    bucket = _s3_bucket()
    if not bucket:
        return []

    try:
        response = _client().get_object(Bucket=bucket, Key=_s3_key(session_id))
        payload = response["Body"].read().decode("utf-8")
        path.write_text(payload, encoding="utf-8")
        return json.loads(payload)
    except (ClientError, BotoCoreError, json.JSONDecodeError):
        return []


def append_conversation(session_id: str, user_message: str, assistant_message: str) -> None:
    history = get_session_history(session_id)
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

    path = _session_path(session_id)
    serialized = json.dumps(history, indent=2)
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
