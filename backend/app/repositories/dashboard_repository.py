"""
Database aggregation queries for dashboard metrics.

This repository is responsible only for summary and aggregation
queries used by the Phase 11 dashboard.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus, DocumentType, WorkflowStatus
from app.db.models.document import Document
from app.db.models.workflow import Workflow


def count_documents(
    database_session: Session,
) -> int:
    """Return the total number of documents."""

    statement = select(func.count(Document.id))

    return database_session.scalar(statement) or 0


def count_documents_by_status(
    database_session: Session,
) -> dict[DocumentStatus, int]:
    """Return document counts grouped by processing status."""

    statement = (
        select(
            Document.status,
            func.count(Document.id),
        )
        .group_by(Document.status)
        .order_by(Document.status)
    )

    rows = database_session.execute(statement).all()

    return {status: count for status, count in rows}


def count_documents_by_type(
    database_session: Session,
) -> dict[DocumentType, int]:
    """Return document counts grouped by document type."""

    statement = (
        select(
            Document.document_type,
            func.count(Document.id),
        )
        .group_by(Document.document_type)
        .order_by(Document.document_type)
    )

    rows = database_session.execute(statement).all()

    return {document_type: count for document_type, count in rows}


def count_workflows(
    database_session: Session,
) -> int:
    """Return the total number of workflows."""

    statement = select(func.count(Workflow.id))

    return database_session.scalar(statement) or 0


def count_workflows_by_status(
    database_session: Session,
) -> dict[WorkflowStatus, int]:
    """Return workflow counts grouped by current status."""

    statement = (
        select(
            Workflow.current_status,
            func.count(Workflow.id),
        )
        .group_by(Workflow.current_status)
        .order_by(Workflow.current_status)
    )

    rows = database_session.execute(statement).all()

    return {status: count for status, count in rows}
