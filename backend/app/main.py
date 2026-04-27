from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.models import ChatRequest, ChatResponse, UploadResponse
from app.services.chat_service import generate_chat_response
from app.services.memory_service import (
    append_conversation,
    get_selected_document,
    get_session_history,
    list_session_documents,
    set_selected_document,
)
from app.services.retriever_service import is_ambiguous_query
from app.services.upload_service import ingest_upload

app = FastAPI(title="StudyBuddy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadResponse:
    document = await ingest_upload(file, session_id=session_id)
    return UploadResponse(**document)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = get_session_history(request.session_id)
    session_documents = list_session_documents(request.session_id)
    session_document_names = [item["document_name"] for item in session_documents]
    selected_document = get_selected_document(request.session_id)
    resolved_document_name = request.document_name or _resolve_explicit_document_name(
        request.message,
        session_document_names,
    )

    if resolved_document_name:
        set_selected_document(request.session_id, resolved_document_name)
    elif len(session_document_names) == 1 and is_ambiguous_query(request.message):
        resolved_document_name = session_document_names[0]
        set_selected_document(request.session_id, resolved_document_name)
    elif selected_document and is_ambiguous_query(request.message):
        resolved_document_name = selected_document
    elif len(session_document_names) > 1 and is_ambiguous_query(request.message):
        return ChatResponse(
            session_id=request.session_id,
            type="disambiguation",
            message="Which document are you referring to?",
            options=session_document_names,
            document_name=selected_document,
        )

    response = generate_chat_response(
        request,
        history=history,
        document_name=resolved_document_name,
    )
    append_conversation(request.session_id, request.message, response.response)
    return response


def _resolve_explicit_document_name(message: str, document_names: list[str]) -> str | None:
    normalized_message = message.lower()
    for document_name in document_names:
        if document_name.lower() in normalized_message:
            return document_name
    return None


handler = Mangum(app)
