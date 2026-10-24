"""Tests for audit-log repository ordering."""

from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType
from app.repositories.audit_log_repository import (
    create_audit_log,
    get_audit_logs_by_entity,
)


def test_audit_logs_are_ordered_by_id(
    db_session: Session,
) -> None:
    """Audit events should follow their database ID order."""

    # Use a test workflow identifier.
    workflow_id = 999999

    # Create two audit events.
    first_log = create_audit_log(
        database_session=db_session,
        user_id=None,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=workflow_id,
    )

    second_log = create_audit_log(
        database_session=db_session,
        user_id=None,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=workflow_id,
    )

    # Retrieve all audit events for the workflow.
    audit_logs = get_audit_logs_by_entity(
        database_session=db_session,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=workflow_id,
    )

    # Confirm the events are returned in ID order.
    assert [log.id for log in audit_logs] == [
        first_log.id,
        second_log.id,
    ]
