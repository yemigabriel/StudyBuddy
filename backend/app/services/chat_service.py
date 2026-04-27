from app.models import ChatRequest, ChatResponse
from app.services.rag_service import retrieve_context


def generate_chat_response(request: ChatRequest) -> ChatResponse:
    context = retrieve_context(request.message)
    if context:
        response = (
            "I found relevant study material for your question.\n\n"
            f"Question: {request.message}\n\n"
            "Most relevant notes:\n"
            + "\n".join(f"- {item}" for item in context)
        )
    else:
        response = (
            "I could not find matching uploaded material yet. "
            "Upload notes first, then ask your question again."
        )

    return ChatResponse(
        response=response,
        session_id=request.session_id,
        context=context,
    )
