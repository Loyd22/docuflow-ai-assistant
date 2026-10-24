"""Tests for transaction-aware audit logging."""

from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType
from app.db.models.audit_log import AuditLog
from app.repositories.audit_log_repository import create_audit_log


def test_audit_log_can_be_flushed_without_commit(
    db_session: Session,
) -> None:
    """An audit event can be rolled back before commit."""

    audit_log = create_audit_log(
        database_session=db_session,
        user_id=None,
        action=AuditAction.WORKFLOW_REVIEW_RESOLVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=123,
        event_metadata={"test": True},
        commit=False,
    )

    # Flush assigns an ID without committing.
    assert audit_log.id is not None

    audit_log_id = audit_log.id

    # Undo the uncommitted change.
    db_session.rollback()

    assert db_session.get(AuditLog, audit_log_id) is None


def test_audit_log_default_commit_still_works(
    db_session: Session,
) -> None:
    """Existing callers can continue using the default behavior."""

    audit_log = create_audit_log(
        database_session=db_session,
        user_id=None,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=123,
    )

    assert audit_log.id is not None

    stored_log = db_session.get(AuditLog, audit_log.id)

    assert stored_log is not None
    assert stored_log.action == AuditAction.WORKFLOW_CREATED
