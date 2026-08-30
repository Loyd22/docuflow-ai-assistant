"""
Approval database model.

Approval records preserve human decisions made during a workflow.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ApprovalDecision

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.workflow import Workflow


class Approval(Base):
    """Represents a human decision made on a workflow."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    approver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(
            ApprovalDecision,
            name="approval_decision",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    workflow: Mapped["Workflow"] = relationship(
        back_populates="approvals",
    )

    approver: Mapped["User"] = relationship(
        back_populates="approvals",
    )
