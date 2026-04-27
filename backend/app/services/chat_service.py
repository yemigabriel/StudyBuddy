from collections.abc import Iterator

from app.models import ChatRequest, ChatResponse, FlashcardsPayload, QuizPayload
from app.services.agent_service import (
    run_flashcard_agent,
    run_quiz_agent,
    run_summary_agent,
)
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
    response = ""
    quiz: QuizPayload | None = None
    flashcards: FlashcardsPayload | None = None

    if request.mode == "summary":
        response = run_summary_agent(context)
    elif request.mode == "quiz":
        quiz = run_quiz_agent(context)
        response = "Quiz generated successfully."
    elif request.mode == "flashcards":
        flashcards = run_flashcard_agent(context)
        response = "Flashcards generated successfully."
    else:
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
        mode=request.mode,
        quiz=quiz,
        flashcards=flashcards,
    )


def generate_chat_stream(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
    document_name: str | None = None,
) -> tuple[list[str], Iterator[str]]:
    if request.mode != "qa":
        raise ValueError("Streaming is only supported for QA mode.")

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
