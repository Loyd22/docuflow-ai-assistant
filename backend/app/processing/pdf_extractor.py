"""
PDF text extractor.

This extractor reads text from PDF pages and returns
the combined contents as a single string.
"""

from pathlib import Path

from pypdf import PdfReader

from app.processing.base_extractor import BaseTextExtractor


class PDFExtractor(BaseTextExtractor):
    """Extract text from PDF documents."""

    def extract(self, file_path: Path) -> str:
        """Read and return text from all readable PDF pages."""

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text and page_text.strip():
                pages.append(page_text.strip())

        return "\n".join(pages)
