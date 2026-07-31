from unittest.mock import patch

from app.config import Settings
from app.services import llm_service


def make_settings(api_key: str | None = None) -> Settings:
    return Settings(
        openai_api_key=api_key,
        vector_db="chroma",
        pinecone_api_key=None,
        pinecone_index_name=None,
        memory_backend="local",
        memory_bucket=None,
        chroma_path="data/chroma",
        chroma_collection_name="studybuddy_chunks",
        embedding_model="text-embedding-3-small",
        chat_model="gpt-4o-mini",
        upload_dir="data/uploads",
        memory_dir="../memory/sessions",
        cors_allow_origins=["*"],
    )


def test_is_standalone_query_flags_follow_up_phrase() -> None:
    assert llm_service.is_standalone_query("what is this document?") is False
    assert llm_service.is_standalone_query("Explain long term potentiation") is True


def test_rewrite_query_returns_original_when_no_history() -> None:
    assert llm_service.rewrite_query("are you sure?", []) == "are you sure?"


@patch("app.services.llm_service.get_settings", return_value=make_settings(api_key=None))
def test_generate_response_returns_helpful_message_when_key_missing(_mock_settings) -> None:
    response = llm_service.generate_response("context", "question")

    assert "OPENAI_API_KEY is not set" in response


@patch("app.services.llm_service.get_settings", return_value=make_settings(api_key=None))
def test_stream_response_returns_single_fallback_chunk_when_key_missing(_mock_settings) -> None:
    chunks = list(llm_service.stream_response("context", "question"))

    assert len(chunks) == 1
    assert "OPENAI_API_KEY is not set" in chunks[0]


def test_build_chat_messages_uses_context_fallback() -> None:
    messages = llm_service._build_chat_messages("", "What is this about?", history=None)

    assert messages[0]["role"] == "system"
    assert "No relevant study material was retrieved." in messages[1]["content"]
