"""
Information request database model.

Tracks additional information requested by a reviewer
and the employee's response.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.workflow import Workflow


class WorkflowInformationRequest(Base):
    """Track an information request and its response."""

    __tablename__ = "workflow_information_requests"

    __table_args__ = (
        # Each request must come from exactly one decision.
        CheckConstraint(
            "(approval_id IS NOT NULL AND review_id IS NULL) OR "
            "(approval_id IS NULL AND review_id IS NOT NULL)",
            name="ck_information_request_one_source",
        ),
        # Responses return only to the correct review queue.
        CheckConstraint(
            "return_status IN ('needs_review', 'pending_approval')",
            name="ck_information_request_return_status",
        ),
        # Prevent multiple unanswered requests for one workflow.
        Index(
            "uq_information_request_one_open_per_workflow",
            "workflow_id",
            unique=True,
            postgresql_where=text("responded_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    # Link the request to exactly one originating decision.
    approval_id: Mapped[int | None] = mapped_column(
        ForeignKey("approvals.id"),
        nullable=True,
        unique=True,
    )

    review_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_reviews.id"),
        nullable=True,
        unique=True,
    )

    # Record who requested the additional information.
    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    request_comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Store the employee's response when submitted.
    response_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    responded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Remember which review queue should receive the response.
    return_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Connect this request to its parent workflow.
    workflow: Mapped["Workflow"] = relationship(
        back_populates="information_requests",
    )
