"""
Business logic for document uploads.

The service layer coordinates file validation, file storage,
and database persistence.
"""

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.repositories.document_repository import create_document
from app.storage.file_storage import (
    generate_stored_file_name,
    save_uploaded_file,
)

ALLOWED_FILE_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file_extension(file_name: str) -> None:
    """Reject files whose extension is not supported."""

    file_extension = Path(file_name).suffix.lower()

    if file_extension not in ALLOWED_FILE_EXTENSIONS:
        allowed_extensions = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))

        raise ValueError(f"Unsupported file type. Allowed types: {allowed_extensions}.")


def validate_file_size(file_path: Path) -> int:
    """Validate the saved file size and return its size in bytes."""

    file_size = file_path.stat().st_size

    if file_size == 0:
        raise ValueError("Uploaded file cannot be empty.")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("Uploaded file exceeds the 10 MB size limit.")

    return file_size


def upload_document(
    database_session: Session,
    *,
    uploaded_file: UploadFile,
    uploaded_by: int,
) -> Document:
    """Validate, store, and persist an uploaded document."""

    original_file_name = uploaded_file.filename

    if not original_file_name:
        raise ValueError("Uploaded file must have a filename.")

    validate_file_extension(original_file_name)

    stored_file_name = generate_stored_file_name(original_file_name)

    saved_file_path = save_uploaded_file(
        uploaded_file=uploaded_file,
        stored_file_name=stored_file_name,
    )

    try:
        file_size = validate_file_size(saved_file_path)

        document = create_document(
            database_session,
            uploaded_by=uploaded_by,
            original_file_name=original_file_name,
            stored_file_name=stored_file_name,
            file_path=str(saved_file_path),
            mime_type=uploaded_file.content_type or "application/octet-stream",
            file_size=file_size,
        )

        return document

    except (ValueError, SQLAlchemyError):
        if saved_file_path.exists():
            saved_file_path.unlink()

        database_session.rollback()

        raise
