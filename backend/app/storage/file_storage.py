"""
Local file-storage utilities for uploaded documents.

This module is responsible for filesystem operations only.
It does not handle database persistence, authentication,
or document-processing business rules.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

UPLOAD_DIRECTORY = Path("uploads")


def ensure_upload_directory_exists() -> None:
    """Create the upload directory if it does not already exist."""

    UPLOAD_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def generate_stored_file_name(original_file_name: str) -> str:
    """Generate a unique internal filename while preserving the extension."""

    file_extension = Path(original_file_name).suffix.lower()

    return f"{uuid4().hex}{file_extension}"


def save_uploaded_file(
    uploaded_file: UploadFile,
    stored_file_name: str,
) -> Path:
    """Save an uploaded file to the local upload directory."""

    ensure_upload_directory_exists()

    destination_path = UPLOAD_DIRECTORY / stored_file_name

    uploaded_file.file.seek(0)

    with destination_path.open("wb") as destination_file:
        while chunk := uploaded_file.file.read(1024 * 1024):
            destination_file.write(chunk)

    return destination_path
