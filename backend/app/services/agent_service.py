import logging
import asyncio

from agents import Agent, Runner

from app.models import FlashcardsPayload, QuizPayload

logger = logging.getLogger(__name__)

SUMMARY_INSTRUCTIONS = """
Summarize the document for a student.

Include:
- key ideas
- important concepts
- concise explanation

Keep it structured and easy to read.
"""

QUIZ_INSTRUCTIONS = """
Generate 3-5 multiple choice questions based on the content.

Return JSON:
{
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer": "correct option"
    }
  ]
}

Ensure:
- questions are clear
- options are distinct
- only one correct answer
"""

FLASHCARD_INSTRUCTIONS = """
Generate 5-8 flashcards from the content.

Each flashcard should:
- have a clear question or concept on the front
- have a concise answer on the back

Return ONLY JSON object:
{
  "cards": [
    { "front": "...", "back": "..." }
  ]
}
"""


def _summary_agent() -> Agent:
    return Agent(
        name="SummaryAgent",
        instructions=SUMMARY_INSTRUCTIONS,
    )


def _quiz_agent() -> Agent:
    return Agent(
        name="QuizAgent",
        instructions=QUIZ_INSTRUCTIONS,
        output_type=QuizPayload,
    )


def _flashcard_agent() -> Agent:
    return Agent(
        name="FlashcardAgent",
        instructions=FLASHCARD_INSTRUCTIONS,
        output_type=FlashcardsPayload,
    )


def _run_agent(agent: Agent, user_input: str):
    return asyncio.run(
        Runner.run(
            agent,
            input=user_input,
        )
    )


def run_summary_agent(context: str) -> str:
    try:
        result = _run_agent(
            _summary_agent(),
            f"Context:\n{context}",
        )
        return str(result.final_output).strip()
    except Exception:
        logger.exception("Summary agent failed.")
        return "I couldn't generate a summary right now. Please try again."


def run_quiz_agent(context: str) -> QuizPayload:
    try:
        result = _run_agent(
            _quiz_agent(),
            f"Context:\n{context}",
        )
        return result.final_output
    except Exception:
        logger.exception("Quiz agent failed.")
        return QuizPayload(questions=[])


def run_flashcard_agent(context: str) -> FlashcardsPayload:
    try:
        result = _run_agent(
            _flashcard_agent(),
            f"Context:\n{context}",
        )
        return result.final_output
    except Exception:
        logger.exception("Flashcard agent failed.")
        return FlashcardsPayload(cards=[])
