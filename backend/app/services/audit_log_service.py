"""
Application service for recording and retrieving audit events.

This service provides a centralized way for other application
services to record important user and system actions and retrieve
audit history for business entities.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType
from app.db.models.audit_log import AuditLog
from app.repositories.audit_log_repository import (
    create_audit_log,
    get_all_audit_logs,
    get_audit_logs_by_entity,
)


class AuditLogService:
    """Coordinate creation and retrieval of immutable audit-log records."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def record_event(
        self,
        *,
        user_id: int | None,
        action: AuditAction,
        entity_type: AuditEntityType,
        entity_id: int | None = None,
        event_metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> AuditLog:
        """Record an audit event in the current database session."""

        return create_audit_log(
            database_session=self.database_session,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=event_metadata,
            commit=commit,
        )

    def get_all_logs(self) -> list[AuditLog]:
        """Return all audit events from newest to oldest."""

        return get_all_audit_logs(
            database_session=self.database_session,
        )

    def get_entity_history(
        self,
        *,
        entity_type: AuditEntityType,
        entity_id: int,
    ) -> list[AuditLog]:
        """Return the chronological audit history for one entity."""

        return get_audit_logs_by_entity(
            database_session=self.database_session,
            entity_type=entity_type,
            entity_id=entity_id,
        )
