from app.services import chunking_service


def test_split_text_returns_empty_for_blank_input() -> None:
    assert chunking_service.split_text("   ") == []


def test_merge_structural_chunks_attaches_headers_to_following_chunk() -> None:
    chunks = ["## Introduction", "This section explains the topic in detail."]

    merged = chunking_service._merge_structural_chunks(chunks)

    assert merged == ["## Introduction\n\nThis section explains the topic in detail."]


def test_merge_structural_chunks_appends_very_short_chunks() -> None:
    chunks = [
        "This is a long enough paragraph to stand on its own in the chunk list.",
        "Short note",
    ]

    merged = chunking_service._merge_structural_chunks(chunks)

    assert merged == [
        "This is a long enough paragraph to stand on its own in the chunk list.\n\nShort note"
    ]
