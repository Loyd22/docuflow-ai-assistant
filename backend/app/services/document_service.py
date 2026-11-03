"""
Business logic for document uploads.

The service layer coordinates file validation, file storage,
database persistence, and document-upload audit logging.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType
from app.db.models.document import Document
from app.repositories.document_repository import (
    create_document,
    get_documents_by_user,
)
from app.services.audit_log_service import AuditLogService
from app.storage.file_storage import (
    generate_stored_file_name,
    save_uploaded_file,
)

if TYPE_CHECKING:
    from app.storage.base import DocumentStorage

logger = logging.getLogger(__name__)

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


def validate_upload_stream_size(uploaded_file: UploadFile) -> int:
    """Validate upload size before sending it to storage."""

    uploaded_file.file.seek(0, 2)
    file_size = uploaded_file.file.tell()
    uploaded_file.file.seek(0)

    if file_size == 0:
        raise ValueError("Uploaded file cannot be empty.")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("Uploaded file exceeds the 10 MB size limit.")

    return file_size


def list_documents(
    database_session: Session,
    *,
    uploaded_by: int,
) -> list[Document]:
    """Return documents belonging to the authenticated user."""

    return get_documents_by_user(
        database_session,
        uploaded_by=uploaded_by,
    )


def upload_document(
    database_session: Session,
    *,
    uploaded_file: UploadFile,
    uploaded_by: int,
    storage: "DocumentStorage | None" = None,
    storage_provider: str = "local",
) -> Document:
    """Validate, store, persist, and audit an uploaded document."""

    original_file_name = uploaded_file.filename

    if not original_file_name:
        raise ValueError("Uploaded file must have a filename.")

    validate_file_extension(original_file_name)

    stored_file_name = generate_stored_file_name(original_file_name)

    saved_file_path: Path | None = None
    storage_key: str | None = None

    # Preserve existing local uploads until storage migration is complete.
    if storage is None:
        saved_file_path = save_uploaded_file(
            uploaded_file=uploaded_file,
            stored_file_name=stored_file_name,
        )

    else:
        # Validate the stream before uploading to the storage provider.
        file_size = validate_upload_stream_size(uploaded_file)

        storage_key = storage.save(
            uploaded_file.file,
            stored_file_name,
        )

    try:
        if saved_file_path is not None:
            file_size = validate_file_size(saved_file_path)
            file_path = str(saved_file_path)

        else:
            # Store the key returned by the selected storage provider.
            assert storage_key is not None
            file_path = storage_key

        # Insert the document without committing.
        document = create_document(
            database_session,
            uploaded_by=uploaded_by,
            original_file_name=original_file_name,
            stored_file_name=stored_file_name,
            file_path=file_path,
            mime_type=(uploaded_file.content_type or "application/octet-stream"),
            file_size=file_size,
            storage_provider=storage_provider,
            commit=False,
        )

        audit_log_service = AuditLogService(
            database_session=database_session,
        )

        # Add the upload audit event to the same transaction.
        audit_log_service.record_event(
            user_id=uploaded_by,
            action=AuditAction.DOCUMENT_UPLOADED,
            entity_type=AuditEntityType.DOCUMENT,
            entity_id=document.id,
            event_metadata={
                "original_file_name": document.original_file_name,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
            },
            commit=False,
        )

        # Commit document metadata and audit event together.
        database_session.commit()

        return document

    except Exception:
        # Roll back the failed database transaction.
        database_session.rollback()

        try:
            # Delete the file created by this upload.
            if storage is not None and storage_key is not None:
                storage.delete(storage_key)

            elif saved_file_path is not None:
                saved_file_path.unlink(missing_ok=True)

        except Exception:  # noqa: BLE001
            # Cleanup is best-effort; preserve the original database error.
            # Do not log the raw SDK exception because it may contain secrets.
            logger.error("Failed to clean up uploaded document after database failure.")

        # Re-raise the original database or audit error.
        raise
