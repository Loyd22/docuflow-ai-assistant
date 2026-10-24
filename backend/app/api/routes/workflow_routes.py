"""
Workflow and approval API endpoints.

These routes expose workflow state, approval decisions,
and manual-review operations through WorkflowService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.enums import UserRole, WorkflowStatus
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.workflow_information_request_repository import (
    get_open_information_request,
)
from app.repositories.workflow_repository import (
    get_all_workflows,
    get_workflow_by_id,
    get_workflows_by_uploader,
)
from app.schemas.workflow_schema import (
    ApprovalDecisionRequest,
    ApprovalResponse,
    WorkflowDecisionResponse,
    WorkflowHistoryResponse,
    WorkflowInformationRequestResponse,
    WorkflowInformationResponseDecisionResponse,
    WorkflowInformationResponseRequest,
    WorkflowResponse,
    WorkflowReviewDecisionResponse,
    WorkflowReviewRequest,
    WorkflowReviewResponse,
)
from app.security.document_access_policy import DocumentAccessPolicy
from app.services.workflow_history_service import WorkflowHistoryService
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

        # Show only workflows this user is allowed to access.
    visible_workflows = [
        workflow
        for workflow in workflows
        if DocumentAccessPolicy.can_view_workflow(
            workflow=workflow,
            current_user=current_user,
        )
    ]

    return [WorkflowResponse.model_validate(workflow) for workflow in visible_workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> WorkflowResponse:
    """Return a workflow only when the user can view it."""

    # Find the requested workflow in the database.
    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    # Return 404 if the workflow does not exist.
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    # Check visibility using the centralized access policy.
    if not DocumentAccessPolicy.can_view_workflow(
        workflow=workflow,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this workflow.",
        )

    # Return the workflow when access is allowed.
    return WorkflowResponse.model_validate(workflow)


@router.get(
    "/{workflow_id}/information-request",
    response_model=WorkflowInformationRequestResponse,
)
def get_workflow_information_request(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> WorkflowInformationRequestResponse:
    """Return an open information request to an authorized user."""

    # Find the workflow linked to the information request.
    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    # Check whether the user can view this workflow.
    if not DocumentAccessPolicy.can_view_workflow(
        workflow=workflow,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this information request.",
        )

    # Only workflows waiting for information have an open request.
    if workflow.current_status != WorkflowStatus.NEEDS_INFORMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow is not waiting for information.",
        )

    # Find the unanswered information request.
    information_request = get_open_information_request(
        database_session=database_session,
        workflow_id=workflow.id,
    )

    if information_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No unanswered information request was found.",
        )

    return WorkflowInformationRequestResponse.model_validate(
        information_request,
    )


@router.get(
    "/{workflow_id}/history",
    response_model=WorkflowHistoryResponse,
)
def get_workflow_history(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> WorkflowHistoryResponse:
    """Return ordered workflow history to authorized users."""

    # Find the workflow.
    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    # Prevent users from viewing restricted workflow history.
    if not DocumentAccessPolicy.can_view_workflow(
        workflow=workflow,
        current_user=current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this workflow history.",
        )

    # Delegate history retrieval and ordering to the service.
    history_service = WorkflowHistoryService(
        database_session=database_session,
    )

    return history_service.get_history(
        workflow_id=workflow.id,
    )


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
    """Record an authorized approval decision."""

    # Find the workflow in the database.
    workflow = get_workflow_by_id(
        database_session=database_session,
        workflow_id=workflow_id,
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    # Create the service responsible for workflow decisions.
    workflow_service = WorkflowService(
        database_session=database_session,
    )

    try:
        # The service checks permissions and saves the decision.
        updated_workflow, approval = workflow_service.record_approval_decision(
            workflow=workflow,
            approver_id=current_user.id,
            decision=request.decision,
            comment=request.comment,
        )

    except PermissionError as error:
        # The manager is not authorized for this workflow.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except InvalidWorkflowStateError as error:
        # The workflow is not waiting for approval.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValueError as error:
        # Return an error when the review information is invalid.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    # Return the updated workflow and saved approval.
    return WorkflowDecisionResponse(
        workflow=WorkflowResponse.model_validate(
            updated_workflow,
        ),
        approval=ApprovalResponse.model_validate(
            approval,
        ),
    )


@router.post(
    "/{workflow_id}/review",
    response_model=WorkflowReviewDecisionResponse,
)
def record_workflow_review(
    workflow_id: int,
    request: WorkflowReviewRequest,
    current_user: User = Depends(
        require_roles(
            UserRole.MANAGER,
            UserRole.ADMIN,
        )
    ),
    database_session: Session = Depends(get_db_session),
) -> WorkflowReviewDecisionResponse:
    """Record a manual-review decision by a manager or admin."""

    # Find the workflow being reviewed.
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
        # Check authorization and save the review.
        updated_workflow, review = workflow_service.record_manual_review(
            workflow=workflow,
            reviewer_id=current_user.id,
            outcome=request.outcome,
            comment=request.comment,
            corrected_total_amount=request.corrected_total_amount,
        )

    except PermissionError as error:
        # The manager is not authorized to review this workflow.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except InvalidWorkflowStateError as error:
        # The workflow is not waiting for manual review.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValueError as error:
        # Return an error when the review information is invalid.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return WorkflowReviewDecisionResponse(
        workflow=WorkflowResponse.model_validate(
            updated_workflow,
        ),
        review=WorkflowReviewResponse.model_validate(
            review,
        ),
    )


@router.post(
    "/{workflow_id}/information-response",
    response_model=WorkflowInformationResponseDecisionResponse,
)
def submit_workflow_information_response(
    workflow_id: int,
    request: WorkflowInformationResponseRequest,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE)),
    database_session: Session = Depends(get_db_session),
) -> WorkflowInformationResponseDecisionResponse:
    """Allow a document owner to answer an information request."""

    # Find the workflow the employee is responding to.
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
        # Validate ownership and save the response.
        updated_workflow, information_request = (
            workflow_service.respond_to_information_request(
                workflow=workflow,
                employee_id=current_user.id,
                response_comment=request.response_comment,
            )
        )

    except PermissionError as error:
        # Employees can respond only to their own documents.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except InvalidWorkflowStateError as error:
        # The workflow is not waiting for information.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValueError as error:
        # Return an error when the review information is invalid.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return WorkflowInformationResponseDecisionResponse(
        workflow=WorkflowResponse.model_validate(
            updated_workflow,
        ),
        information_request=(
            WorkflowInformationRequestResponse.model_validate(
                information_request,
            )
        ),
    )
