from app.models import ChatRequest, ChatResponse


def build_basic_response(request: ChatRequest) -> ChatResponse:
    response = (
        "StudyBuddy received your message: "
        f"'{request.message}'. RAG and memory will be added in the next stages."
    )
    return ChatResponse(response=response, session_id=request.session_id)
