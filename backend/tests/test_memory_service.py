import tempfile
from pathlib import Path
from unittest.mock import patch

from app.services import memory_service


def test_normalize_state_handles_legacy_message_list() -> None:
    payload = [{"role": "user", "content": "hello"}]

    normalized = memory_service._normalize_state(payload)

    assert normalized["messages"] == payload
    assert normalized["documents"] == []
    assert normalized["selected_document"] is None


def test_add_session_document_deduplicates_document_name() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(memory_service, "MEMORY_DIR", Path(tmpdir)):
            with patch("app.services.memory_service._upload_to_s3"):
                memory_service.add_session_document("abc", "doc-1", "notes.pdf")
                memory_service.add_session_document("abc", "doc-2", "notes.pdf")

                documents = memory_service.list_session_documents("abc")

    assert len(documents) == 1
    assert documents[0]["document_name"] == "notes.pdf"


def test_append_conversation_writes_user_and_assistant_messages() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(memory_service, "MEMORY_DIR", Path(tmpdir)):
            with patch("app.services.memory_service._upload_to_s3"):
                memory_service.append_conversation("session-1", "Hi", "Hello")
                history = memory_service.get_session_history("session-1")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[0]["content"] == "Hi"
    assert history[1]["content"] == "Hello"
