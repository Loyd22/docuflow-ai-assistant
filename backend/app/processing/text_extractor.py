"""
Plain-text document extractor.

This extractor reads UTF-8 encoded .txt files and returns their contents.
"""

from pathlib import Path

from app.processing.base_extractor import BaseTextExtractor


class TextExtractor(BaseTextExtractor):
    """Extract text from plain-text documents."""

    def extract(self, file_path: Path) -> str:
        """Read and return the contents of a UTF-8 text file."""

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        return file_path.read_text(encoding="utf-8")
