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


def get_stored_file_path(stored_file_name: str) -> Path:
    """Return a safely validated path to an uploaded file."""

    # Stored filenames must be simple filenames, not paths.
    if (
        not stored_file_name
        or stored_file_name != Path(stored_file_name).name
        or "/" in stored_file_name
        or "\\" in stored_file_name
    ):
        raise ValueError("Invalid stored file name.")

    # Find the upload directory's absolute location.
    upload_directory = UPLOAD_DIRECTORY.resolve()

    # Resolve the requested file's real location.
    file_path = (upload_directory / stored_file_name).resolve()

    # Prevent reading files outside the upload directory.
    if not file_path.is_relative_to(upload_directory):
        raise ValueError("Invalid stored file path.")

    # Only allow existing regular files.
    if not file_path.is_file():
        raise FileNotFoundError("Original document file not found.")

    return file_path
