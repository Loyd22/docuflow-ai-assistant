"""
Microsoft Word DOCX text extractor.

This extractor reads paragraphs from .docx documents
and returns their text as a single string.
"""

from pathlib import Path

from docx import Document

from app.processing.base_extractor import BaseTextExtractor


class DOCXExtractor(BaseTextExtractor):
    """Extract text from Microsoft Word DOCX documents."""

    def extract(self, file_path: Path) -> str:
        """Read paragraph text from a DOCX document."""

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        document = Document(file_path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)
