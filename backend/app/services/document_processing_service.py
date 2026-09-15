"""
Document processing service.

Coordinates text extraction from uploaded documents,
tracks processing status, and persists the result.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.processing.exceptions import DocumentProcessingError
from app.processing.extractor_factory import ExtractorFactory
from app.repositories.document_repository import save_document


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

        return save_document(
            database_session,
            document,
        )

    except Exception as error:
        document.status = DocumentStatus.PROCESSING_FAILED

        save_document(
            database_session,
            document,
        )

        if isinstance(error, DocumentProcessingError):
            raise

        raise DocumentProcessingError("Document processing failed.") from error
