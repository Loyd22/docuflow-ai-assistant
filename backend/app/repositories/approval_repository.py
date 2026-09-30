"""
Database access functions for workflow approvals.

The repository layer is responsible only for approval persistence
and retrieval. It should not contain authorization rules,
HTTP logic, or workflow state-transition decisions.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import ApprovalDecision
from app.db.models.approval import Approval


def create_approval(
    database_session: Session,
    *,
    workflow_id: int,
    approver_id: int,
    decision: ApprovalDecision,
    comment: str | None = None,
) -> Approval:
    """Create and persist a workflow approval decision."""

    approval = Approval(
        workflow_id=workflow_id,
        approver_id=approver_id,
        decision=decision,
        comment=comment,
    )

    database_session.add(approval)
    database_session.commit()
    database_session.refresh(approval)

    return approval


def get_approvals_by_workflow_id(
    database_session: Session,
    workflow_id: int,
) -> list[Approval]:
    """Return all approval decisions recorded for a workflow."""

    statement = (
        select(Approval)
        .where(Approval.workflow_id == workflow_id)
        .order_by(Approval.created_at.asc())
    )

    return list(database_session.scalars(statement))
