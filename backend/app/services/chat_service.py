from collections.abc import Iterator

from app.models import ChatRequest, ChatResponse
from app.services.llm_service import generate_response, rewrite_query, stream_response
from app.services.retriever_service import build_context, retrieve_context


def prepare_chat_context(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
    document_name: str | None = None,
) -> tuple[list[str], str]:
    retrieval_query = rewrite_query(request.message, (history or [])[-2:])
    chunks = retrieve_context(
        retrieval_query,
        document_name=document_name,
    )
    context = build_context(chunks)
    return chunks, context


def generate_chat_response(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
    document_name: str | None = None,
) -> ChatResponse:
    chunks, context = prepare_chat_context(
        request,
        history=history,
        document_name=document_name,
    )
    response = generate_response(
        context,
        request.message,
        history=history,
    )

    return ChatResponse(
        response=response,
        session_id=request.session_id,
        context=chunks,
        document_name=document_name,
    )


def generate_chat_stream(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
    document_name: str | None = None,
) -> tuple[list[str], Iterator[str]]:
    chunks, context = prepare_chat_context(
        request,
        history=history,
        document_name=document_name,
    )
    return chunks, stream_response(
        context,
        request.message,
        history=history,
    )
