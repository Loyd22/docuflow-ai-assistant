"""Shared contract for document storage providers."""

from pathlib import Path
from typing import BinaryIO, Protocol


class DocumentStorage(Protocol):
    """Operations every document storage provider must support."""

    def save(
        self,
        source: BinaryIO,
        stored_name: str,
    ) -> str:
        """Save a file and return its storage key."""
        ...

    def download_to_path(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        """Copy a stored file to a local destination."""
        ...

    def delete(self, storage_key: str) -> None:
        """Delete a stored file."""
        ...
