"""
Document extractor factory.

Chooses the correct text extractor based on a document's file extension.
"""

from pathlib import Path

from app.processing.base_extractor import BaseTextExtractor
from app.processing.docx_extractor import DOCXExtractor
from app.processing.pdf_extractor import PDFExtractor
from app.processing.text_extractor import TextExtractor


class ExtractorFactory:
    """Create the correct text extractor for a supported file type."""

    @staticmethod
    def get_extractor(file_path: Path) -> BaseTextExtractor:
        """Return the appropriate extractor based on file extension."""

        extension = file_path.suffix.lower()

        if extension == ".txt":
            return TextExtractor()

        if extension == ".docx":
            return DOCXExtractor()

        if extension == ".pdf":
            return PDFExtractor()

        raise ValueError(f"Unsupported file type: {extension}")
