"""
Audit-log API endpoints.

These routes expose Phase 11 audit history while delegating
audit-log retrieval to AuditLogService.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.enums import AuditEntityType, UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.audit_log_schema import AuditLogResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    current_user: User = Depends(
        require_roles(
            UserRole.MANAGER,
            UserRole.ADMIN,
        )
    ),
    database_session: Session = Depends(get_db_session),
) -> list[AuditLogResponse]:
    """Return all audit logs for managers and administrators."""

    audit_log_service = AuditLogService(
        database_session=database_session,
    )

    audit_logs = audit_log_service.get_all_logs()

    return [AuditLogResponse.model_validate(audit_log) for audit_log in audit_logs]


@router.get(
    "/{entity_type}/{entity_id}",
    response_model=list[AuditLogResponse],
)
def get_entity_audit_history(
    entity_type: AuditEntityType,
    entity_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.MANAGER,
            UserRole.ADMIN,
        )
    ),
    database_session: Session = Depends(get_db_session),
) -> list[AuditLogResponse]:
    """Return audit history for one entity."""

    audit_log_service = AuditLogService(
        database_session=database_session,
    )

    audit_logs = audit_log_service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
    )

    return [AuditLogResponse.model_validate(audit_log) for audit_log in audit_logs]
