import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    vector_db: str
    pinecone_api_key: str | None
    pinecone_index_name: str | None
    chroma_path: str
    chroma_collection_name: str
    embedding_model: str
    chat_model: str


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        vector_db=os.getenv("VECTOR_DB", "chroma").strip().lower(),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME"),
        chroma_path=os.getenv("CHROMA_PATH", "data/chroma"),
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "studybuddy_chunks"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
    )
