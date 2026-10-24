"""
Database access functions for manual workflow reviews.

The repository stores and retrieves review records.
The service layer controls when changes are committed.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import ReviewOutcome
from app.db.models.workflow_review import WorkflowReview


def create_workflow_review(
    database_session: Session,
    *,
    workflow_id: int,
    reviewer_id: int,
    outcome: ReviewOutcome,
    comment: str,
) -> WorkflowReview:
    """Stage a manual-review decision in the current transaction."""

    review = WorkflowReview(
        workflow_id=workflow_id,
        reviewer_id=reviewer_id,
        outcome=outcome,
        comment=comment,
    )

    # Add the review without committing the transaction.
    database_session.add(review)
    database_session.flush()

    return review


def get_reviews_by_workflow_id(
    database_session: Session,
    *,
    workflow_id: int,
) -> list[WorkflowReview]:
    """Return the manual-review history of a workflow."""

    statement = (
        select(WorkflowReview)
        .where(WorkflowReview.workflow_id == workflow_id)
        .order_by(
            WorkflowReview.created_at.asc(),
            WorkflowReview.id.asc(),
        )
    )

    return list(database_session.scalars(statement).all())
