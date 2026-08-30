import json
import os
import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mangum import Mangum

from app.config import get_settings
from app.models import ChatRequest, ChatResponse, MemoryPreviewResponse, UploadResponse
from app.services.chat_service import generate_chat_response, generate_chat_stream
from app.services.memory_service import (
    append_conversation,
    get_selected_document,
    get_session_history,
    get_session_state,
    list_session_documents,
    set_selected_document,
)
from app.services.retriever_service import is_ambiguous_query
from app.services.upload_service import ingest_upload

settings = get_settings()
app = FastAPI(title="StudyBuddy API", version="0.1.0")

security = HTTPBearer()

CLERK_JWT_PUBLIC_KEY = os.getenv("CLERK_JWT_PUBLIC_KEY")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")

jwks_client = PyJWKClient(CLERK_JWKS_URL) if CLERK_JWKS_URL else None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print(f"token is {token}")
    try:
        if not jwks_client:
            print("no public key set")
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "dev_fallback_user")
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"signing key: {signing_key}")
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        print(f"user_id is {user_id}")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed authorization payload. Missing user id")
        return user_id
    except jwt.ExpiredSignatureError:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, 
             detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied. Invalid authentication signature.")    

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
) -> UploadResponse:
    try:
        document = await ingest_upload(file, session_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UploadResponse(**document)


@app.get("/memory", response_model=MemoryPreviewResponse)
def memory_preview(user_id: str = Depends(get_current_user)) -> MemoryPreviewResponse:
    state = get_session_state(user_id)
    return MemoryPreviewResponse(
        session_id=user_id,
        selected_document=state.get("selected_document"),
        documents=state.get("documents", []),
        messages=state.get("messages", []),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user_id: str = Depends(get_current_user)) -> ChatResponse:
    request.session_id = user_id
    history, resolved_document_name, disambiguation = _resolve_chat_context(request)
    if disambiguation:
        return disambiguation

    response = generate_chat_response(
        request,
        history=history,
        document_name=resolved_document_name,
    )
    append_conversation(request.session_id, request.message, response.response)
    return response


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, user_id: str = Depends(get_current_user)) -> StreamingResponse:
    request.session_id = user_id
    history, resolved_document_name, disambiguation = _resolve_chat_context(request)
    if disambiguation:
        def disambiguation_stream() -> str:
            yield _sse_event(
                "disambiguation",
                {
                    "session_id": disambiguation.session_id,
                    "message": disambiguation.message,
                    "options": disambiguation.options,
                    "document_name": disambiguation.document_name,
                },
            )

        return StreamingResponse(disambiguation_stream(), media_type="text/event-stream")

    if request.mode != "qa":
        response = generate_chat_response(
            request,
            history=history,
            document_name=resolved_document_name,
        )
        append_conversation(request.session_id, request.message, response.response)

        def mode_stream() -> str:
            yield _sse_event(
                "metadata",
                {
                    "session_id": request.session_id,
                    "context": response.context,
                    "document_name": resolved_document_name,
                    "mode": request.mode,
                },
            )
            if response.quiz is not None:
                yield _sse_event(
                    "quiz",
                    {
                        "questions": [question.model_dump() for question in response.quiz.questions],
                    },
                )
            if response.flashcards is not None:
                yield _sse_event(
                    "flashcards",
                    {
                        "cards": [card.model_dump() for card in response.flashcards.cards],
                    },
                )
            yield _sse_event(
                "done",
                {
                    "response": response.response,
                    "session_id": request.session_id,
                    "document_name": resolved_document_name,
                    "mode": request.mode,
                },
            )

        return StreamingResponse(mode_stream(), media_type="text/event-stream")

    chunks, token_stream = generate_chat_stream(
        request,
        history=history,
        document_name=resolved_document_name,
    )

    def stream_events() -> str:
        full_response = ""
        yield _sse_event(
            "metadata",
            {
                "session_id": request.session_id,
                "context": chunks,
                "document_name": resolved_document_name,
                "mode": request.mode,
            },
        )
        for token in token_stream:
            full_response += token
            yield _sse_event("chunk", {"content": token})
        append_conversation(request.session_id, request.message, full_response)
        yield _sse_event(
            "done",
            {
                "response": full_response,
                "session_id": request.session_id,
                "document_name": resolved_document_name,
                "mode": request.mode,
            },
        )

    return StreamingResponse(stream_events(), media_type="text/event-stream")


def _resolve_chat_context(
    request: ChatRequest,
) -> tuple[list[dict[str, str]], str | None, ChatResponse | None]:
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
        return history, resolved_document_name, ChatResponse(
            session_id=request.session_id,
            type="disambiguation",
            message="Which document are you referring to?",
            options=session_document_names,
            document_name=selected_document,
        )
    return history, resolved_document_name, None


def _resolve_explicit_document_name(message: str, document_names: list[str]) -> str | None:
    normalized_message = message.lower()
    for document_name in document_names:
        if document_name.lower() in normalized_message:
            return document_name
    return None


def _sse_event(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


handler = Mangum(app)
