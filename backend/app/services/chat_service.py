from app.models import ChatRequest, ChatResponse
from app.services.rag_service import retrieve_context


def generate_chat_response(
    request: ChatRequest,
    history: list[dict[str, str]] | None = None,
) -> ChatResponse:
    context = retrieve_context(request.message)
    history = history or []
    prior_turns = len(history) // 2

    if context:
        response = (
            "I found relevant study material for your question.\n\n"
            f"Question: {request.message}\n\n"
            f"Previous turns in this session: {prior_turns}\n\n"
            "Most relevant notes:\n"
            + "\n".join(f"- {item}" for item in context)
        )
    else:
        response = (
            "I could not find matching uploaded material yet. "
            f"This session currently has {prior_turns} previous turns. "
            "Upload notes first, then ask your question again."
        )

    return ChatResponse(
        response=response,
        session_id=request.session_id,
        context=context,
    )
