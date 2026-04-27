import logging
from collections.abc import Iterator

from openai import OpenAI, OpenAIError

from app.config import get_settings

logger = logging.getLogger(__name__)

FOLLOW_UP_PATTERNS = (
    "this",
    "that",
    "it",
    "they",
    "them",
    "those",
    "these",
)


def is_standalone_query(query: str) -> bool:
    normalized = query.strip().lower()
    if not normalized:
        return True

    words = normalized.split()
    if len(words) <= 6 and any(token in words for token in FOLLOW_UP_PATTERNS):
        return False

    vague_phrases = (
        "what is this document",
        "what is this file",
        "what does it say",
        "what is it about",
        "explain this",
        "explain it",
        "tell me more about it",
        "are you sure",
    )
    return not any(phrase in normalized for phrase in vague_phrases)


def rewrite_query(current_query: str, chat_history: list[dict]) -> str:
    if is_standalone_query(current_query):
        return current_query

    if not chat_history:
        return current_query

    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        return current_query

    history_lines = []
    for message in chat_history[-2:]:
        role = message.get("role", "user")
        content = message.get("content", "").strip()
        if content:
            history_lines.append(f"{role}: {content}")

    if not history_lines:
        return current_query

    client = OpenAI(api_key=api_key)
    logger.info("Generating rewritten query using OpenAI with model %s.", settings.chat_model)
    try:
        response = client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a query rewriting assistant.\n\n"
                        "Given a conversation history and a follow-up question, "
                        "rewrite the question into a clear, standalone query that "
                        "can be used for document retrieval.\n\n"
                        "Keep it concise and specific.\n\n"
                        f"Conversation:\n{chr(10).join(history_lines)}\n\n"
                        f"Follow-up question:\n{current_query}\n\n"
                        "Rewritten query:"
                    ),
                }
            ],
        )
    except OpenAIError:
        logger.error("Error occurred while generating rewritten query.", exc_info=True)
        return current_query

    message = response.choices[0].message.content
    if not message:
        return current_query

    rewritten = message.strip()
    return rewritten or current_query


def _build_chat_messages(
    context: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    if not context.strip():
        context = "No relevant study material was retrieved."

    history_lines = []
    for message in (history or [])[-2:]:
        role = message.get("role", "user")
        content = message.get("content", "").strip()
        if content:
            history_lines.append(f"{role}: {content}")

    history_text = "\n".join(history_lines) if history_lines else "No recent conversation."
    return [
        {
            "role": "system",
            "content": (
                """
                You are StudyBuddy, a helpful study assistant.
                Use the provided context when it is relevant. 
                If the context is insufficient, say so clearly and avoid inventing facts.
                Use the context below to answer the question.

                You may summarize or infer the answer if it is clearly supported by the context.

                If the answer truly cannot be derived from the context, say:
                "I don't know based on the provided document."
            """
            ),
        },
        {
            "role": "user",
            "content": (
                f"Recent conversation:\n{history_text}\n\n"
                f"Context:\n{context}\n\n"
                f"Question:\n{question}"
            ),
        },
    ]


def generate_response(
    context: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        return (
            "OPENAI_API_KEY is not set. Add it to your environment and try again."
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=settings.chat_model,
            messages=_build_chat_messages(
                context,
                question,
                history=history,
            ),
        )
    except OpenAIError:
        logger.error("Error occurred while generating response from OpenAI.", exc_info=True)
        return (
            "I couldn't generate a response from OpenAI right now. "
            "Please try again."
        )

    message = response.choices[0].message.content
    if not message:
        return "I couldn't generate a response from OpenAI right now. Please try again."

    return message.strip()


def stream_response(
    context: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> Iterator[str]:
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        yield "OPENAI_API_KEY is not set. Add it to your environment and try again."
        return

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=settings.chat_model,
            messages=_build_chat_messages(
                context,
                question,
                history=history,
            ),
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except OpenAIError:
        logger.error("Error occurred while streaming response from OpenAI.", exc_info=True)
        yield "I couldn't generate a response from OpenAI right now. Please try again."
