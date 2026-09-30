"""
Database access functions for workflows.

The repository layer is responsible only for workflow persistence
and database retrieval. It should not contain HTTP logic,
authorization rules, or workflow business decisions.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import WorkflowPriority, WorkflowStatus
from app.db.models.workflow import Workflow


def create_workflow(
    database_session: Session,
    *,
    document_id: int,
    current_status: WorkflowStatus,
    priority: WorkflowPriority = WorkflowPriority.NORMAL,
    recommended_action: str | None = None,
    assigned_to: int | None = None,
) -> Workflow:
    """Create and persist a workflow for a document."""

    workflow = Workflow(
        document_id=document_id,
        current_status=current_status,
        priority=priority,
        recommended_action=recommended_action,
        assigned_to=assigned_to,
    )

    database_session.add(workflow)
    database_session.commit()
    database_session.refresh(workflow)

    return workflow


def get_workflow_by_id(
    database_session: Session,
    workflow_id: int,
) -> Workflow | None:
    """Return a workflow by ID, or None when it does not exist."""

    return database_session.get(Workflow, workflow_id)


def get_workflow_by_document_id(
    database_session: Session,
    document_id: int,
) -> Workflow | None:
    """Return the workflow associated with a document."""

    statement = select(Workflow).where(
        Workflow.document_id == document_id,
    )

    return database_session.scalar(statement)


def update_workflow_status(
    database_session: Session,
    workflow: Workflow,
    status: WorkflowStatus,
) -> Workflow:
    """Update and persist a workflow's current status."""

    workflow.current_status = status

    database_session.add(workflow)
    database_session.commit()
    database_session.refresh(workflow)

    return workflow


def save_workflow(
    database_session: Session,
    workflow: Workflow,
) -> Workflow:
    """Persist changes made to an existing workflow."""

    database_session.add(workflow)
    database_session.commit()
    database_session.refresh(workflow)

    return workflow
