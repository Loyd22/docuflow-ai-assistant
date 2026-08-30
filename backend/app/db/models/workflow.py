"""
Workflow database model.

A workflow tracks the current business-processing state of a document.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import WorkflowPriority, WorkflowStatus

if TYPE_CHECKING:
    from app.db.models.approval import Approval
    from app.db.models.document import Document
    from app.db.models.user import User


class Workflow(Base):
    """Represents the processing and approval workflow for a document."""

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    current_status: Mapped[WorkflowStatus] = mapped_column(
        Enum(
            WorkflowStatus,
            name="workflow_status",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=WorkflowStatus.NEEDS_REVIEW,
        nullable=False,
        index=True,
    )

    priority: Mapped[WorkflowPriority] = mapped_column(
        Enum(
            WorkflowPriority,
            name="workflow_priority",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=WorkflowPriority.NORMAL,
        nullable=False,
        index=True,
    )

    recommended_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
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

    document: Mapped["Document"] = relationship(
        back_populates="workflow",
    )

    assignee: Mapped["User | None"] = relationship(
        back_populates="assigned_workflows",
        foreign_keys=[assigned_to],
    )

    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="workflow",
    )
