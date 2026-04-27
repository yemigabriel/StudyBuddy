from app.models import ChatRequest, ChatResponse
from app.services.llm_service import generate_response, rewrite_query
from app.services.retriever_service import build_context, retrieve_context


def generate_chat_response(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
    document_name: str | None = None,
) -> ChatResponse:
    retrieval_query = rewrite_query(request.message, (history or [])[-2:])
    chunks = retrieve_context(
        retrieval_query,
        document_name=document_name,
    )
    context = build_context(chunks)
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
