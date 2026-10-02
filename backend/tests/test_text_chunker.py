import pytest

from app.rag.chunker import TextChunker


def test_short_text_returns_single_chunk() -> None:
    chunker = TextChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.split("This is a short document.")

    assert chunks == ["This is a short document."]


def test_plain_text_creates_overlapping_character_chunks() -> None:
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=3,
    )

    chunks = chunker.split("abcdefghijklmnopqrstuvwxyz")

    assert chunks == [
        "abcdefghij",
        "hijklmnopq",
        "opqrstuvwx",
        "vwxyz",
    ]


def test_structured_text_prefers_paragraph_boundaries() -> None:
    chunker = TextChunker(
        chunk_size=50,
        chunk_overlap=10,
    )

    text = (
        "Annual Leave\n\n"
        "Employees receive 15 days of leave.\n\n"
        "Remote Work\n\n"
        "Employees may work remotely."
    )

    chunks = chunker.split(text)

    assert chunks == [
        ("Annual Leave\n\nEmployees receive 15 days of leave."),
        ("Remote Work\n\nEmployees may work remotely."),
    ]


def test_paragraph_overlap_reuses_small_trailing_paragraph() -> None:
    chunker = TextChunker(
        chunk_size=50,
        chunk_overlap=15,
    )

    text = (
        "Section One\n\nFirst paragraph text.\n\nSection Two\n\nSecond paragraph text."
    )

    chunks = chunker.split(text)

    assert "Section Two" in chunks[-1]


def test_empty_text_returns_empty_list() -> None:
    chunker = TextChunker()

    chunks = chunker.split("   ")

    assert chunks == []


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="Chunk overlap must be smaller than chunk size.",
    ):
        TextChunker(
            chunk_size=100,
            chunk_overlap=100,
        )


def test_chunk_size_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="Chunk size must be greater than zero.",
    ):
        TextChunker(
            chunk_size=0,
            chunk_overlap=0,
        )


def test_chunk_overlap_cannot_be_negative() -> None:
    with pytest.raises(
        ValueError,
        match="Chunk overlap cannot be negative.",
    ):
        TextChunker(
            chunk_size=100,
            chunk_overlap=-1,
        )
