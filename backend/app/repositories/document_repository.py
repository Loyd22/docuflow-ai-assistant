"""
Database access functions for documents.

The repository layer is responsible only for database operations.
It should not contain file-storage logic, HTTP logic, or business rules.
"""

from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus, DocumentType
from app.db.models.document import Document


def create_document(
    database_session: Session,
    *,
    uploaded_by: int,
    original_file_name: str,
    stored_file_name: str,
    file_path: str,
    mime_type: str,
    file_size: int,
    document_type: DocumentType = DocumentType.UNKNOWN,
    status: DocumentStatus = DocumentStatus.UPLOADED,
) -> Document:
    """Create and persist a new document record."""

    document = Document(
        uploaded_by=uploaded_by,
        original_file_name=original_file_name,
        stored_file_name=stored_file_name,
        file_path=file_path,
        mime_type=mime_type,
        file_size=file_size,
        document_type=document_type,
        status=status,
    )

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    return document


def save_document(
    database_session: Session,
    document: Document,
) -> Document:
    """Persist changes made to an existing document."""

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    return document


def get_document_by_id(
    database_session: Session,
    document_id: int,
) -> Document | None:
    """Return a document by ID, or None when it does not exist."""

    return database_session.get(Document, document_id)
