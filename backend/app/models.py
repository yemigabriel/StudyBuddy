from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str


class QuizPayload(BaseModel):
    questions: list[QuizQuestion]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    document_name: str | None = None
    mode: str = "qa"


class ChatResponse(BaseModel):
    response: str = ""
    session_id: str
    context: list[str] = []
    type: str = "answer"
    message: str | None = None
    options: list[str] = []
    document_name: str | None = None
    mode: str = "qa"
    quiz: QuizPayload | None = None


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    filename: str
    content_type: str
    size: int
    parsed_chunks: int
    chunks: int
    indexing_status: str
    error: str | None = None
