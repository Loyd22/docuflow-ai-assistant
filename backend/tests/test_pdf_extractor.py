"""
Tests for PDF text extraction.
"""

from pathlib import Path

import pytest

from app.processing.pdf_extractor import PDFExtractor


def test_extract_raises_error_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    """The extractor should reject missing PDF files."""

    file_path = tmp_path / "missing.pdf"

    extractor = PDFExtractor()

    with pytest.raises(FileNotFoundError):
        extractor.extract(file_path)


def test_extract_raises_error_when_path_is_directory(
    tmp_path: Path,
) -> None:
    """The extractor should reject directory paths."""

    extractor = PDFExtractor()

    with pytest.raises(ValueError):
        extractor.extract(tmp_path)
