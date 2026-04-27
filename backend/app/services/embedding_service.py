import logging

from openai import OpenAI, OpenAIError

from app.config import get_settings

logger = logging.getLogger(__name__)


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [text.strip() for text in texts if text.strip()]
    if not cleaned:
        logger.info("Embedding skipped because no non-empty texts were provided.")
        return []

    settings = get_settings()
    if not settings.openai_api_key:
        logger.error("Embedding failed because OPENAI_API_KEY is not set.")
        raise ValueError("OPENAI_API_KEY is not set.")

    logger.info(
        "Generating embeddings for %s text chunk(s) using model %s.",
        len(cleaned),
        settings.embedding_model,
    )
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=cleaned,
            encoding_format="float",
        )
    except OpenAIError as exc:
        logger.exception("OpenAI embedding request failed.")
        raise RuntimeError("Failed to generate embeddings.") from exc

    logger.info("Successfully generated %s embedding vector(s).", len(response.data))
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    embeddings = embed_texts([text])
    return embeddings[0] if embeddings else []
