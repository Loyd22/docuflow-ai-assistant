"""
Database model for manual workflow reviews.

Stores human review outcomes separately from approval decisions.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ReviewOutcome

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.workflow import Workflow


class WorkflowReview(Base):
    """Stores one manual-review decision."""

    __tablename__ = "workflow_reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    outcome: Mapped[ReviewOutcome] = mapped_column(
        Enum(
            ReviewOutcome,
            name="review_outcome",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )

    comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    workflow: Mapped["Workflow"] = relationship(
        back_populates="reviews",
    )

    reviewer: Mapped["User"] = relationship()
