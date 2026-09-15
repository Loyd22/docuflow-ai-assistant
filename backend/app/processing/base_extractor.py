"""
Base interface for document text extractors.

Every document extractor in DocuFlow should follow the same contract:
receive a file path and return the extracted text as a string.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseTextExtractor(ABC):
    """Define the interface that all text extractors must implement."""

    @abstractmethod
    def extract(self, file_path: Path) -> str:
        """Extract text from the document located at file_path."""
        raise NotImplementedError
