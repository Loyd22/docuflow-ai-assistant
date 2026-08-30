"""
User database model.

The User table stores application accounts and their authorization role.
Authentication logic itself does not belong here.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import UserRole

if TYPE_CHECKING:
    from app.db.models.approval import Approval
    from app.db.models.audit_log import AuditLog
    from app.db.models.document import Document
    from app.db.models.workflow import Workflow


class User(Base):
    """Represents a DocuFlow application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=UserRole.EMPLOYEE,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="uploader",
    )

    assigned_workflows: Mapped[list["Workflow"]] = relationship(
        back_populates="assignee",
        foreign_keys="Workflow.assigned_to",
    )

    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="approver",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
    )
