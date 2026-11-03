"""
Document processing service.

Coordinates text extraction, processing status,
database persistence, and audit logging.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session

from app.db.enums import (
    AuditAction,
    AuditEntityType,
    DocumentStatus,
)
from app.db.models.document import Document
from app.processing.exceptions import DocumentProcessingError
from app.processing.extractor_factory import ExtractorFactory
from app.repositories.document_repository import save_document
from app.services.audit_log_service import AuditLogService
from app.storage.base import DocumentStorage


def extract_document_text(file_path: Path) -> str:
    """Extract text using the existing document extractors."""

    extractor = ExtractorFactory.get_extractor(file_path)
    return extractor.extract(file_path)


def process_document(
    database_session: Session,
    document: Document,
    *,
    storage: DocumentStorage | None = None,
) -> Document:
    """Extract text from a local or stored document."""

    document.status = DocumentStatus.PROCESSING

    save_document(
        database_session,
        document,
    )

    try:
        if storage is None:
            # Keep the existing local-file behavior.
            file_path = Path(document.file_path)
            extracted_text = extract_document_text(file_path)

        else:
            # Keep the extension for the existing extractor factory.
            extension = Path(document.stored_file_name).suffix.lower()

            if extension not in {".pdf", ".docx", ".txt"}:
                raise DocumentProcessingError("Unsupported document extension.")

            # TemporaryDirectory removes files after processing.
            with TemporaryDirectory() as temporary_directory:
                file_path = Path(temporary_directory) / f"document{extension}"

                # Retrieve the document from the storage provider.
                storage.download_to_path(
                    document.stored_file_name,
                    file_path,
                )

                extracted_text = extract_document_text(file_path)

        if not extracted_text.strip():
            raise DocumentProcessingError(
                "No extractable text was found in the document."
            )

        document.extracted_text = extracted_text
        document.status = DocumentStatus.TEXT_EXTRACTED

        updated_document = save_document(
            database_session,
            document,
        )

        audit_log_service = AuditLogService(
            database_session=database_session,
        )

        audit_log_service.record_event(
            user_id=None,
            action=AuditAction.DOCUMENT_TEXT_EXTRACTED,
            entity_type=AuditEntityType.DOCUMENT,
            entity_id=updated_document.id,
            event_metadata={
                "status": updated_document.status.value,
                "extracted_character_count": len(extracted_text),
            },
        )

        return updated_document

    except Exception as error:
        document.status = DocumentStatus.PROCESSING_FAILED

        save_document(
            database_session,
            document,
        )

        if isinstance(error, DocumentProcessingError):
            raise

        raise DocumentProcessingError("Document processing failed.") from error
