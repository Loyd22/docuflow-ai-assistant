"""
Database access functions for audit logs.

The repository layer is responsible only for audit-log persistence
and retrieval. It should not contain authorization rules,
HTTP logic, or decisions about which actions should be audited.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType
from app.db.models.audit_log import AuditLog


def create_audit_log(
    database_session: Session,
    *,
    user_id: int | None,
    action: AuditAction,
    entity_type: AuditEntityType,
    entity_id: int | None = None,
    event_metadata: dict[str, Any] | None = None,
    commit: bool = True,
) -> AuditLog:
    """Create an audit event, optionally without committing."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=event_metadata,
    )

    database_session.add(audit_log)

    if commit:
        # Preserve existing behavior for other services.
        database_session.commit()
        database_session.refresh(audit_log)
    else:
        # Save within the current transaction without committing.
        database_session.flush()

    return audit_log


def get_audit_logs_by_entity(
    database_session: Session,
    *,
    entity_type: AuditEntityType,
    entity_id: int,
) -> list[AuditLog]:
    """Return audit events in a consistent sequence."""

    statement = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        # IDs provide a deterministic event sequence.
        .order_by(AuditLog.id.asc())
    )

    return list(database_session.scalars(statement))


def get_all_audit_logs(
    database_session: Session,
) -> list[AuditLog]:
    """Return all audit logs ordered from newest to oldest."""

    statement = select(AuditLog).order_by(
        AuditLog.created_at.desc(),
    )

    return list(database_session.scalars(statement).all())
