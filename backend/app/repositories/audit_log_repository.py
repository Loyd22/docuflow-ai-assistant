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
) -> AuditLog:
    """Create and persist an audit-log entry."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=event_metadata,
    )

    database_session.add(audit_log)
    database_session.commit()
    database_session.refresh(audit_log)

    return audit_log


def get_audit_logs_by_entity(
    database_session: Session,
    *,
    entity_type: AuditEntityType,
    entity_id: int,
) -> list[AuditLog]:
    """Return audit logs for a specific entity."""

    statement = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.created_at.asc())
    )

    return list(database_session.scalars(statement))
