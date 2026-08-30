"""
Audit log database model.

Audit logs record important user and system actions so business
activity can be traced later.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import AuditAction, AuditEntityType

if TYPE_CHECKING:
    from app.db.models.user import User


class AuditLog(Base):
    """Represents an immutable record of an important system action."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            name="audit_action",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[AuditEntityType] = mapped_column(
        Enum(
            AuditEntityType,
            name="audit_entity_type",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User | None"] = relationship(
        back_populates="audit_logs",
    )
