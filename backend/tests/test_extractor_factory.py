"""
Tests for document extractor selection.
"""

from pathlib import Path

import pytest

from app.processing.docx_extractor import DOCXExtractor
from app.processing.extractor_factory import ExtractorFactory
from app.processing.pdf_extractor import PDFExtractor
from app.processing.text_extractor import TextExtractor


def test_returns_text_extractor_for_txt_file() -> None:
    """TXT files should use TextExtractor."""

    extractor = ExtractorFactory.get_extractor(Path("document.txt"))

    assert isinstance(extractor, TextExtractor)


def test_returns_docx_extractor_for_docx_file() -> None:
    """DOCX files should use DOCXExtractor."""

    extractor = ExtractorFactory.get_extractor(Path("document.docx"))

    assert isinstance(extractor, DOCXExtractor)


def test_returns_pdf_extractor_for_pdf_file() -> None:
    """PDF files should use PDFExtractor."""

    extractor = ExtractorFactory.get_extractor(Path("document.pdf"))

    assert isinstance(extractor, PDFExtractor)


def test_file_extension_is_case_insensitive() -> None:
    """Uppercase extensions should still be recognized."""

    extractor = ExtractorFactory.get_extractor(Path("document.PDF"))

    assert isinstance(extractor, PDFExtractor)


def test_unsupported_file_type_raises_error() -> None:
    """Unsupported file extensions should be rejected."""

    with pytest.raises(ValueError, match="Unsupported file type"):
        ExtractorFactory.get_extractor(Path("document.xlsx"))
