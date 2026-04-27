from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import logging
from uuid import uuid4

import chromadb
from chromadb.config import Settings as ChromaSettings
from pinecone import Pinecone

from app.config import get_settings
from app.services.embedding_service import embed_text, embed_texts

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    id: str
    document: str
    metadata: dict
    score: float


class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, docs: list[str], metadatas: list[dict] | None = None) -> int:
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        query: str,
        k: int = 5,
        document_name: str | None = None,
    ) -> list[SearchResult]:
        raise NotImplementedError


class ChromaStore(VectorStore):
    def __init__(self) -> None:
        settings = get_settings()
        logger.info("Initializing ChromaStore at %s.", settings.chroma_path)
        client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def add_documents(self, docs: list[str], metadatas: list[dict] | None = None) -> int:
        texts = [doc for doc in docs if doc.strip()]
        if not texts:
            logger.warning("Chroma add_documents received no non-empty chunks.")
            return 0

        logger.info("Adding %s chunk(s) to Chroma.", len(texts))
        embeddings = embed_texts(texts)
        payload_metadatas = metadatas or [{} for _ in texts]
        ids = [str(uuid4()) for _ in texts]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=payload_metadatas,
        )
        logger.info("Stored %s chunk(s) in Chroma.", len(texts))
        return len(texts)

    def query(
        self,
        query: str,
        k: int = 5,
        document_name: str | None = None,
    ) -> list[SearchResult]:
        query_embedding = embed_text(query)
        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if document_name:
            query_args["where"] = {"document_name": document_name}

        result = self.collection.query(
            **query_args,
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        matches: list[SearchResult] = []
        for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            matches.append(
                SearchResult(
                    id=item_id,
                    document=document or "",
                    metadata=metadata or {},
                    score=1 - float(distance or 0.0),
                )
            )
        return matches


class PineconeStore(VectorStore):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.pinecone_api_key or not settings.pinecone_index_name:
            raise ValueError(
                "PINECONE_API_KEY and PINECONE_INDEX_NAME are required for Pinecone."
            )

        logger.info("Initializing PineconeStore for index %s.", settings.pinecone_index_name)
        client = Pinecone(api_key=settings.pinecone_api_key)
        self.index = client.Index(settings.pinecone_index_name)

    def add_documents(self, docs: list[str], metadatas: list[dict] | None = None) -> int:
        texts = [doc for doc in docs if doc.strip()]
        if not texts:
            logger.warning("Pinecone add_documents received no non-empty chunks.")
            return 0

        logger.info("Adding %s chunk(s) to Pinecone.", len(texts))
        embeddings = embed_texts(texts)
        payload_metadatas = metadatas or [{} for _ in texts]
        vectors = []
        for text, embedding, metadata in zip(texts, embeddings, payload_metadatas):
            vector_metadata = dict(metadata)
            vector_metadata["text"] = text
            vectors.append(
                {
                    "id": str(uuid4()),
                    "values": embedding,
                    "metadata": vector_metadata,
                }
            )

        self.index.upsert(vectors=vectors)
        logger.info("Stored %s chunk(s) in Pinecone.", len(vectors))
        return len(vectors)

    def query(
        self,
        query: str,
        k: int = 10,
        document_name: str | None = None,
    ) -> list[SearchResult]:
        query_embedding = embed_text(query)
        query_args = {
            "vector": query_embedding,
            "top_k": k,
            "include_metadata": True,
        }
        if document_name:
            query_args["filter"] = {"document_name": {"$eq": document_name}}

        result = self.index.query(**query_args)

        matches: list[SearchResult] = []
        for match in result.matches:
            metadata = dict(match.metadata or {})
            matches.append(
                SearchResult(
                    id=match.id,
                    document=str(metadata.get("text", "")),
                    metadata=metadata,
                    score=float(match.score or 0.0),
                )
            )
        return matches


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    settings = get_settings()
    if settings.vector_db == "pinecone":
        return PineconeStore()
    return ChromaStore()
