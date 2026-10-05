"""
Pydantic schemas for audit-log operations.

These schemas define the audit information exposed through
Phase 11 audit-log API operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.enums import AuditAction, AuditEntityType


class AuditLogResponse(BaseModel):
    """Public representation of an audit-log record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: AuditAction
    entity_type: AuditEntityType
    entity_id: int | None
    event_metadata: dict[str, Any] | None
    created_at: datetime
