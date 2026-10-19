"""
Workflow and approval API endpoints.

These routes expose Phase 9 workflow state and human approval
operations while delegating workflow behavior to WorkflowService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.workflow_repository import (
    get_all_workflows,
    get_workflow_by_id,
    get_workflows_by_uploader,
)
from app.schemas.workflow_schema import (
    ApprovalDecisionRequest,
    ApprovalResponse,
    WorkflowDecisionResponse,
    WorkflowResponse,
)
from app.services.workflow_service import (
    InvalidWorkflowStateError,
    WorkflowService,
)

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@router.get(
    "",
    response_model=list[WorkflowResponse],
)
def list_workflows(
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> list[WorkflowResponse]:
    """Return workflows visible to the authenticated user."""

    if current_user.role == UserRole.EMPLOYEE:
        workflows = get_workflows_by_uploader(
            database_session=database_session,
            uploaded_by=current_user.id,
        )
    else:
        workflows = get_all_workflows(
            database_session=database_session,
        )

    return [WorkflowResponse.model_validate(workflow) for workflow in workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> WorkflowResponse:
    """Return a workflow when the authenticated user is allowed to view it."""

    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    if (
        current_user.role == UserRole.EMPLOYEE
        and workflow.document.uploaded_by != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this workflow.",
        )

    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{workflow_id}/decision",
    response_model=WorkflowDecisionResponse,
)
def record_workflow_decision(
    workflow_id: int,
    request: ApprovalDecisionRequest,
    current_user: User = Depends(
        require_roles(
            UserRole.MANAGER,
            UserRole.ADMIN,
        )
    ),
    database_session: Session = Depends(get_db_session),
) -> WorkflowDecisionResponse:
    """Record an authorized approval decision for a workflow."""

    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    workflow_service = WorkflowService(
        database_session=database_session,
    )

    try:
        updated_workflow, approval = workflow_service.record_approval_decision(
            workflow=workflow,
            approver_id=current_user.id,
            decision=request.decision,
            comment=request.comment,
        )

    except InvalidWorkflowStateError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return WorkflowDecisionResponse(
        workflow=WorkflowResponse.model_validate(
            updated_workflow,
        ),
        approval=ApprovalResponse.model_validate(
            approval,
        ),
    )
