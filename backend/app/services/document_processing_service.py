"""
Document processing service.

Coordinates text extraction from uploaded documents,
tracks processing status, persists the result, and records
successful text-extraction audit events.
"""

from pathlib import Path

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


def process_document(
    database_session: Session,
    document: Document,
) -> Document:
    """Extract document text and update processing status."""

    document.status = DocumentStatus.PROCESSING

    save_document(
        database_session,
        document,
    )

    try:
        file_path = Path(document.file_path)

        extractor = ExtractorFactory.get_extractor(file_path)

        extracted_text = extractor.extract(file_path)

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
