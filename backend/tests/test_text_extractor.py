"""
Tests for plain-text document extraction.
"""

from pathlib import Path

import pytest

from app.processing.text_extractor import TextExtractor


def test_extract_returns_text_file_contents(tmp_path: Path) -> None:
    """The extractor should return the complete text file contents."""

    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "DocuFlow document processing test.",
        encoding="utf-8",
    )

    extractor = TextExtractor()

    result = extractor.extract(file_path)

    assert result == "DocuFlow document processing test."


def test_extract_raises_error_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    """The extractor should reject missing files."""

    file_path = tmp_path / "missing.txt"

    extractor = TextExtractor()

    with pytest.raises(FileNotFoundError):
        extractor.extract(file_path)


def test_extract_raises_error_when_path_is_directory(
    tmp_path: Path,
) -> None:
    """The extractor should reject directory paths."""

    extractor = TextExtractor()

    with pytest.raises(ValueError):
        extractor.extract(tmp_path)
