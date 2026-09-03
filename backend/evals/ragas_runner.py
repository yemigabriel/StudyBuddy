from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


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


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def build_reference_contexts(case: dict, fixtures_dir: Path) -> list[str]:
    from app.services.chunking_service import split_text

    fixture_path = fixtures_dir / case["document_name"]
    if not fixture_path.exists():
        return []

    chunks = split_text(fixture_path.read_text(encoding="utf-8"))
    reference_contexts: list[str] = []
    for fragment in case["expected_retrieval_fragments"]:
        normalized_fragment = normalize_text(fragment)
        matching_chunk = next(
            (
                chunk
                for chunk in chunks
                if normalized_fragment in normalize_text(chunk)
            ),
            None,
        )
        if matching_chunk and matching_chunk not in reference_contexts:
            reference_contexts.append(matching_chunk)

    return reference_contexts


async def score_case(case: dict, fixtures_dir: Path) -> dict[str, float | str]:
    from app.services import retriever_service
    from ragas.dataset_schema import SingleTurnSample
    from ragas.metrics._context_precision import NonLLMContextPrecisionWithReference
    from ragas.metrics._context_recall import NonLLMContextRecall

    retriever_service.get_vector_store = lambda: (_ for _ in ()).throw(
        RuntimeError("Fixture evals bypass vector store queries.")
    )
    retrieved_chunks = retriever_service.retrieve_context(
        case["query"],
        document_name=case["document_name"],
    )
    reference_contexts = build_reference_contexts(case, fixtures_dir)

    if not reference_contexts:
        return {
            "name": case["name"],
            "context_precision": 0.0,
            "context_recall": 0.0,
        }

    sample = SingleTurnSample(
        user_input=case["query"],
        retrieved_contexts=retrieved_chunks,
        reference_contexts=reference_contexts,
        reference=" ".join(case.get("expected_answer_fragments", [])) or None,
        response="",
    )

    context_precision = await NonLLMContextPrecisionWithReference().single_turn_ascore(sample)
    context_recall = await NonLLMContextRecall().single_turn_ascore(sample)

    return {
        "name": case["name"],
        "context_precision": float(context_precision),
        "context_recall": float(context_recall),
    }


async def run_cases(cases: list[dict], fixtures_dir: Path) -> list[dict[str, float | str]]:
    results: list[dict[str, float | str]] = []
    for case in cases:
        results.append(await score_case(case, fixtures_dir))
    return results


def print_summary(results: list[dict[str, float | str]]) -> int:
    print("StudyBuddy Ragas report")
    print("=======================")
    for result in results:
        print(
            f"{result['name']}: "
            f"context_precision={result['context_precision']:.3f}, "
            f"context_recall={result['context_recall']:.3f}"
        )

    average_precision = sum(float(item["context_precision"]) for item in results) / len(results)
    average_recall = sum(float(item["context_recall"]) for item in results) / len(results)

    print("\nAggregate Ragas metrics")
    print("-----------------------")
    print(f"Context Precision: {average_precision:.3f}")
    print(f"Context Recall: {average_recall:.3f}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run StudyBuddy Ragas evals.")
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
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    fixtures_dir = Path(args.fixtures).resolve()

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    if not fixtures_dir.exists():
        print(f"Fixture directory not found: {fixtures_dir}", file=sys.stderr)
        return 1

    cases = load_cases(dataset_path)
    original_upload_dir = os.environ.get("UPLOAD_DIR")

    with tempfile.TemporaryDirectory(prefix="studybuddy-ragas-") as tmpdir:
        upload_dir = Path(tmpdir)
        os.environ["UPLOAD_DIR"] = str(upload_dir)
        stage_fixture_documents(fixtures_dir, upload_dir)
        results = asyncio.run(run_cases(cases, fixtures_dir))

    if original_upload_dir is None:
        os.environ.pop("UPLOAD_DIR", None)
    else:
        os.environ["UPLOAD_DIR"] = original_upload_dir

    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
