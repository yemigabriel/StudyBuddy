from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.models import ChatRequest, ChatResponse, UploadResponse
from app.services.chat_service import build_basic_response
from app.services.upload_service import save_upload

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
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    document = await save_upload(file)
    return UploadResponse(**document)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return build_basic_response(request)


handler = Mangum(app)
