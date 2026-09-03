from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evals.scoring import (
    EvalResult,
    RetrievalMetrics,
    calculate_retrieval_metrics,
    score_answer,
    score_retrieval,
)


def load_cases(dataset_path: Path) -> list[dict]:
    cases: list[dict] = []
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cases.append(json.loads(stripped))
    return cases


def stage_fixture_documents(fixtures_dir: Path, upload_dir: Path) -> None:
    upload_dir.mkdir(parents=True, exist_ok=True)
    for source_path in fixtures_dir.glob("*"):
        if source_path.is_file():
            destination = upload_dir / f"fixture-{source_path.name}"
            shutil.copyfile(source_path, destination)


def run_eval_case(case: dict, include_answers: bool) -> tuple[list[EvalResult], RetrievalMetrics]:
    from app.services.llm_service import generate_response
    from app.services import retriever_service

    retriever_service.get_vector_store = lambda: (_ for _ in ()).throw(
        RuntimeError("Fixture evals bypass vector store queries.")
    )

    retrieved_chunks = retriever_service.retrieve_context(
        case["query"],
        document_name=case["document_name"],
    )
    metrics = calculate_retrieval_metrics(
        retrieved_chunks=retrieved_chunks,
        expected_fragments=case["expected_retrieval_fragments"],
    )
    results = [
        score_retrieval(
            case_name=case["name"],
            retrieved_chunks=retrieved_chunks,
            expected_fragments=case["expected_retrieval_fragments"],
        )
    ]

    if include_answers:
        answer = generate_response(
            retriever_service.build_context(retrieved_chunks),
            case["query"],
            history=case.get("history"),
        )
        results.append(
            score_answer(
                case_name=case["name"],
                answer=answer,
                expected_fragments=case.get("expected_answer_fragments", []),
                forbidden_fragments=case.get("forbidden_answer_fragments", []),
            )
        )

    return results, metrics


def print_summary(
    results: list[EvalResult],
    retrieval_metrics: list[tuple[str, RetrievalMetrics]],
    include_answers: bool,
    allow_failures: bool,
) -> int:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed

    print("StudyBuddy eval report")
    print("=====================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.category}: {result.name} - {result.details}")

    if retrieval_metrics:
        print("\nRetrieval metrics")
        print("-----------------")
        for case_name, metrics in retrieval_metrics:
            rank = metrics.first_relevant_rank if metrics.first_relevant_rank is not None else "none"
            print(
                f"{case_name}: "
                f"precision={metrics.precision:.2f}, "
                f"recall={metrics.recall:.2f}, "
                f"hit_rate={metrics.hit_rate:.2f}, "
                f"mrr={metrics.mrr:.2f}, "
                f"first_relevant_rank={rank}"
            )

        average_precision = sum(item.precision for _, item in retrieval_metrics) / len(retrieval_metrics)
        average_recall = sum(item.recall for _, item in retrieval_metrics) / len(retrieval_metrics)
        average_hit_rate = sum(item.hit_rate for _, item in retrieval_metrics) / len(retrieval_metrics)
        average_mrr = sum(item.mrr for _, item in retrieval_metrics) / len(retrieval_metrics)

        print("\nAggregate retrieval metrics")
        print("---------------------------")
        print(f"Precision: {average_precision:.3f}")
        print(f"Recall: {average_recall:.3f}")
        print(f"Hit Rate: {average_hit_rate:.3f}")
        print(f"MRR: {average_mrr:.3f}")

    if not include_answers:
        print("\nAnswer evals skipped.")

    print(f"\nPassed {passed}/{total} checks.")
    return 0 if allow_failures or failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run StudyBuddy RAG evals.")
    parser.add_argument(
        "--dataset",
        default="evals/dataset.jsonl",
        help="Path to the eval dataset JSONL file.",
    )
    parser.add_argument(
        "--fixtures",
        default="evals/fixtures",
        help="Directory containing fixture documents for retrieval evals.",
    )
    parser.add_argument(
        "--skip-answer",
        action="store_true",
        help="Skip answer generation checks and only run retrieval evals.",
    )
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Report failures without returning a nonzero exit code.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    fixtures_dir = Path(args.fixtures).resolve()
    include_answers = not args.skip_answer and bool(os.getenv("OPENAI_API_KEY"))

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    if not fixtures_dir.exists():
        print(f"Fixture directory not found: {fixtures_dir}", file=sys.stderr)
        return 1

    cases = load_cases(dataset_path)
    original_upload_dir = os.environ.get("UPLOAD_DIR")

    with tempfile.TemporaryDirectory(prefix="studybuddy-evals-") as tmpdir:
        upload_dir = Path(tmpdir)
        os.environ["UPLOAD_DIR"] = str(upload_dir)
        stage_fixture_documents(fixtures_dir, upload_dir)

        all_results: list[EvalResult] = []
        all_retrieval_metrics: list[tuple[str, RetrievalMetrics]] = []
        for case in cases:
            case_results, case_metrics = run_eval_case(case, include_answers=include_answers)
            all_results.extend(case_results)
            all_retrieval_metrics.append((case["name"], case_metrics))

    if original_upload_dir is None:
        os.environ.pop("UPLOAD_DIR", None)
    else:
        os.environ["UPLOAD_DIR"] = original_upload_dir

    return print_summary(
        all_results,
        all_retrieval_metrics,
        include_answers=include_answers,
        allow_failures=args.allow_failures,
    )


if __name__ == "__main__":
    raise SystemExit(main())
