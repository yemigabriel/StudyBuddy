from pathlib import Path

from evals.runner import load_cases
from evals.scoring import calculate_retrieval_metrics, score_answer, score_retrieval


def test_score_retrieval_passes_when_expected_fragments_are_present() -> None:
    result = score_retrieval(
        case_name="biology-mitosis",
        retrieved_chunks=[
            "Mitosis is the process where one cell divides into two genetically identical daughter cells.",
            "The main phases are prophase, metaphase, anaphase, and telophase.",
        ],
        expected_fragments=[
            "two genetically identical daughter cells",
            "prophase, metaphase, anaphase, and telophase",
        ],
    )

    assert result.passed is True
    assert result.score == 1.0


def test_score_answer_fails_when_forbidden_content_is_present() -> None:
    result = score_answer(
        case_name="bad-answer",
        answer="Binary search works best on unsorted lists.",
        expected_fragments=["binary search"],
        forbidden_fragments=["unsorted lists"],
    )

    assert result.passed is False
    assert result.score == 0.0
    assert "forbidden content present" in result.details


def test_calculate_retrieval_metrics_reports_precision_recall_hit_rate_and_mrr() -> None:
    metrics = calculate_retrieval_metrics(
        retrieved_chunks=[
            "This chunk is unrelated.",
            "Mitosis is the process where one cell divides into two genetically identical daughter cells.",
            "The main phases are prophase, metaphase, anaphase, and telophase.",
            "Another unrelated chunk.",
        ],
        expected_fragments=[
            "two genetically identical daughter cells",
            "prophase, metaphase, anaphase, and telophase",
        ],
    )

    assert metrics.precision == 0.5
    assert metrics.recall == 1.0
    assert metrics.hit_rate == 1.0
    assert metrics.mrr == 0.5
    assert metrics.first_relevant_rank == 2


def test_load_cases_reads_dataset() -> None:
    cases = load_cases(Path("evals/dataset.jsonl"))

    assert len(cases) >= 3
    assert cases[0]["name"] == "transformer-core-idea"
