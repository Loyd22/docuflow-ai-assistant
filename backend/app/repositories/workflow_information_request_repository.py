"""
Database access for workflow information requests.

This repository saves requests and employee responses.
Business rules and authorization belong to the service layer.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.workflow_information_request import (
    WorkflowInformationRequest,
)


def create_information_request(
    database_session: Session,
    *,
    workflow_id: int,
    requested_by: int,
    request_comment: str,
    return_status: str,
    approval_id: int | None = None,
    review_id: int | None = None,
) -> WorkflowInformationRequest:
    """Create an information request without committing."""

    information_request = WorkflowInformationRequest(
        workflow_id=workflow_id,
        approval_id=approval_id,
        review_id=review_id,
        requested_by=requested_by,
        request_comment=request_comment,
        return_status=return_status,
    )

    database_session.add(information_request)

    # Obtain its ID while keeping the transaction open.
    database_session.flush()

    return information_request


def get_open_information_request(
    database_session: Session,
    workflow_id: int,
    *,
    for_update: bool = False,
) -> WorkflowInformationRequest | None:
    """Find the unanswered request for a workflow."""

    statement = select(WorkflowInformationRequest).where(
        WorkflowInformationRequest.workflow_id == workflow_id,
        WorkflowInformationRequest.responded_at.is_(None),
    )

    if for_update:
        # Lock the request while processing an employee response.
        statement = statement.with_for_update()

    return database_session.scalar(statement)


def get_information_requests_by_workflow_id(
    database_session: Session,
    workflow_id: int,
) -> list[WorkflowInformationRequest]:
    """Return the information-request history."""

    statement = (
        select(WorkflowInformationRequest)
        .where(WorkflowInformationRequest.workflow_id == workflow_id)
        .order_by(
            WorkflowInformationRequest.requested_at.asc(),
            WorkflowInformationRequest.id.asc(),
        )
    )

    return list(database_session.scalars(statement))


def record_information_response(
    database_session: Session,
    *,
    information_request: WorkflowInformationRequest,
    responded_by: int,
    response_comment: str,
) -> WorkflowInformationRequest:
    """Save an employee response without committing."""

    information_request.response_comment = response_comment
    information_request.responded_by = responded_by
    information_request.responded_at = datetime.now(timezone.utc)

    database_session.add(information_request)

    # The service will commit this alongside the workflow update.
    database_session.flush()

    return information_request
