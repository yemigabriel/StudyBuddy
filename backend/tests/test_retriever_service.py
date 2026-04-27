from app.services.retriever_service import (
    SearchResult,
    build_context,
    is_ambiguous_query,
    is_document_overview_query,
    keyword_overlap,
    merge_results,
    normalize_chunk_text,
    select_fallback_chunks,
    trim_context,
)


def test_merge_results_deduplicates_by_normalized_text_and_keeps_higher_score() -> None:
    low_score = SearchResult(
        id="1",
        document="## Introduction",
        metadata={},
        score=0.2,
    )
    high_score = SearchResult(
        id="2",
        document="##   Introduction  ",
        metadata={},
        score=0.9,
    )

    merged = merge_results([low_score, high_score])

    assert len(merged) == 1
    assert merged[0].score == 0.9


def test_trim_context_limits_total_characters() -> None:
    trimmed = trim_context(["abcdef", "ghijkl"], max_chars=8)

    assert trimmed == ["abcdef", "gh"]


def test_build_context_joins_chunks_with_blank_line() -> None:
    built = build_context(["alpha", "beta"], max_chars=100)

    assert built == "alpha\n\nbeta"


def test_keyword_overlap_scores_shared_terms() -> None:
    score = keyword_overlap({"attention", "model"}, {"attention", "paper"})

    assert score == 0.5


def test_overview_and_ambiguity_detection_cover_common_queries() -> None:
    assert is_document_overview_query("what is this document about?") is True
    assert is_ambiguous_query("explain this") is True
    assert is_ambiguous_query("Explain Hebbian learning") is False


def test_select_fallback_chunks_prefers_abstract_for_overview_queries() -> None:
    chunks = [
        "## References\n\nA list of sources.",
        "## Abstract\n\nThis study presents a compact overview of the method.",
        "## Appendix\n\nExtra notes.",
    ]

    selected = select_fallback_chunks(
        chunks,
        "what is this document?",
        final_k=1,
        overview_query=True,
    )

    assert selected == ["## Abstract\n\nThis study presents a compact overview of the method."]


def test_normalize_chunk_text_collapses_whitespace() -> None:
    assert normalize_chunk_text("A   spaced\nchunk ") == "a spaced chunk"
