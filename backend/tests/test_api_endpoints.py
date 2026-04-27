import json
from typing import Iterator

from fastapi.testclient import TestClient

from app.main import app
from app.models import ChatResponse


client = TestClient(app)


def parse_sse_events(raw_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in [part for part in raw_text.split("\n\n") if part.strip()]:
        lines = block.splitlines()
        event_line = next((line for line in lines if line.startswith("event: ")), None)
        data_line = next((line for line in lines if line.startswith("data: ")), None)
        if not event_line or not data_line:
            continue
        events.append(
            (
                event_line.replace("event: ", "", 1).strip(),
                json.loads(data_line.replace("data: ", "", 1)),
            )
        )
    return events


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_endpoint_returns_ingest_payload(monkeypatch) -> None:
    async def fake_ingest_upload(file, session_id: str) -> dict:
        return {
            "document_id": "doc-1",
            "document_name": file.filename,
            "filename": "stored-notes.md",
            "content_type": file.content_type or "text/markdown",
            "size": 12,
            "parsed_chunks": 2,
            "chunks": 2,
            "indexing_status": "indexed",
            "error": None,
        }

    monkeypatch.setattr("app.main.ingest_upload", fake_ingest_upload)

    response = client.post(
        "/upload",
        data={"session_id": "session-1"},
        files={"file": ("notes.md", b"hello world", "text/markdown")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "doc-1"
    assert body["indexing_status"] == "indexed"


def test_chat_endpoint_returns_standard_qa_response(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr("app.main.list_session_documents", lambda _session_id: [])
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    def fake_generate_chat_response(request, history=None, document_name=None):
        return ChatResponse(
            response="Answer text",
            session_id=request.session_id,
            context=["chunk-1"],
            document_name=document_name,
            mode=request.mode,
        )

    monkeypatch.setattr("app.main.generate_chat_response", fake_generate_chat_response)

    response = client.post(
        "/chat",
        json={"message": "Explain this concept", "session_id": "session-1", "mode": "qa"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "Answer text"
    assert body["mode"] == "qa"


def test_chat_endpoint_returns_disambiguation_when_multiple_documents_exist(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr(
        "app.main.list_session_documents",
        lambda _session_id: [
            {"document_name": "alpha.pdf"},
            {"document_name": "beta.pdf"},
        ],
    )
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.is_ambiguous_query", lambda _query: True)

    response = client.post(
        "/chat",
        json={"message": "what is this document?", "session_id": "session-1", "mode": "qa"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "disambiguation"
    assert body["options"] == ["alpha.pdf", "beta.pdf"]


def test_chat_endpoint_uses_single_session_document_for_ambiguous_query(monkeypatch) -> None:
    selected_documents: list[str | None] = []

    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr(
        "app.main.list_session_documents",
        lambda _session_id: [{"document_name": "alpha.pdf"}],
    )
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: "alpha.pdf")
    monkeypatch.setattr("app.main.is_ambiguous_query", lambda _query: True)
    monkeypatch.setattr(
        "app.main.set_selected_document",
        lambda _session_id, document_name: selected_documents.append(document_name),
    )
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    def fake_generate_chat_response(request, history=None, document_name=None):
        return ChatResponse(
            response="Remembered document answer",
            session_id=request.session_id,
            context=["chunk-1"],
            document_name=document_name,
            mode=request.mode,
        )

    monkeypatch.setattr("app.main.generate_chat_response", fake_generate_chat_response)

    response = client.post(
        "/chat",
        json={"message": "explain this", "session_id": "session-1", "mode": "qa"},
    )

    assert response.status_code == 200
    assert response.json()["document_name"] == "alpha.pdf"
    assert selected_documents == ["alpha.pdf"]


def test_chat_stream_returns_qa_sse_events(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr("app.main.list_session_documents", lambda _session_id: [])
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    def fake_generate_chat_stream(request, history=None, document_name=None):
        return ["chunk-a"], iter(["Hello", " world"])

    monkeypatch.setattr("app.main.generate_chat_stream", fake_generate_chat_stream)

    response = client.post(
        "/chat/stream",
        json={"message": "Hi", "session_id": "session-1", "mode": "qa"},
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0][0] == "metadata"
    assert events[1] == ("chunk", {"content": "Hello"})
    assert events[2] == ("chunk", {"content": " world"})
    assert events[-1][0] == "done"
    assert events[-1][1]["response"] == "Hello world"


def test_chat_stream_returns_summary_mode_done_event(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr("app.main.list_session_documents", lambda _session_id: [])
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    monkeypatch.setattr(
        "app.main.generate_chat_response",
        lambda request, history=None, document_name=None: ChatResponse(
            response="Structured summary",
            session_id=request.session_id,
            context=["chunk-a"],
            document_name=document_name,
            mode=request.mode,
        ),
    )

    response = client.post(
        "/chat/stream",
        json={"message": "Summarize this document.", "session_id": "session-1", "mode": "summary"},
    )

    events = parse_sse_events(response.text)
    assert events[0][0] == "metadata"
    assert events[-1][0] == "done"
    assert events[-1][1]["response"] == "Structured summary"


def test_chat_stream_returns_quiz_event(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr("app.main.list_session_documents", lambda _session_id: [])
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    monkeypatch.setattr(
        "app.main.generate_chat_response",
        lambda request, history=None, document_name=None: ChatResponse(
            response="Quiz generated successfully.",
            session_id=request.session_id,
            context=["chunk-a"],
            document_name=document_name,
            mode=request.mode,
            quiz={
                "questions": [
                    {
                        "question": "Q1",
                        "options": ["A", "B", "C", "D"],
                        "answer": "B",
                    }
                ]
            },
        ),
    )

    response = client.post(
        "/chat/stream",
        json={"message": "Generate a quiz.", "session_id": "session-1", "mode": "quiz"},
    )

    events = parse_sse_events(response.text)
    assert any(event == "quiz" for event, _payload in events)


def test_chat_stream_returns_flashcards_event(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_session_history", lambda _session_id: [])
    monkeypatch.setattr("app.main.list_session_documents", lambda _session_id: [])
    monkeypatch.setattr("app.main.get_selected_document", lambda _session_id: None)
    monkeypatch.setattr("app.main.append_conversation", lambda *args, **kwargs: None)

    monkeypatch.setattr(
        "app.main.generate_chat_response",
        lambda request, history=None, document_name=None: ChatResponse(
            response="Flashcards generated successfully.",
            session_id=request.session_id,
            context=["chunk-a"],
            document_name=document_name,
            mode=request.mode,
            flashcards={
                "cards": [
                    {
                        "front": "Selective Attention",
                        "back": "Filtering relevant stimuli.",
                    }
                ]
            },
        ),
    )

    response = client.post(
        "/chat/stream",
        json={"message": "Generate flashcards.", "session_id": "session-1", "mode": "flashcards"},
    )

    events = parse_sse_events(response.text)
    assert any(event == "flashcards" for event, _payload in events)
