"""
Database access functions for documents.

The repository layer is responsible only for database operations.
It should not contain file-storage logic, HTTP logic, or business rules.
"""

from typing import Any

from sqlalchemy.orm import Session, selectinload

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


def update_document_status(
    database_session: Session,
    document: Document,
    status: DocumentStatus,
) -> Document:
    """Update and persist a document's processing status."""

    document.status = status

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    return document


def update_ai_analysis(
    database_session: Session,
    document: Document,
    document_type: DocumentType,
    classification_confidence: float,
    extracted_data: dict[str, Any] | None,
) -> Document:
    """Persist AI classification and structured extraction results."""

    document.document_type = document_type
    document.classification_confidence = classification_confidence
    document.extracted_data = extracted_data

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    return document


def update_business_rule_result(
    database_session: Session,
    document: Document,
    business_rule_result: dict[str, Any],
) -> Document:
    """Persist a document's evaluated business-rule decision."""

    document.business_rule_result = business_rule_result

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    return document


def get_documents_by_user(
    database_session: Session,
    uploaded_by: int,
) -> list[Document]:
    """Return documents uploaded by a specific user."""

    return (
        database_session.query(Document)
        .options(selectinload(Document.chunks))
        .filter(Document.uploaded_by == uploaded_by)
        .order_by(Document.created_at.desc())
        .all()
    )
