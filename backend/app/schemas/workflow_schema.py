"""
Pydantic schemas for workflow and approval operations.

These schemas define the data exposed through Phase 9 workflow
and approval API operations.
"""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.db.enums import (
    ApprovalDecision,
    ReviewOutcome,
    WorkflowPriority,
    WorkflowStatus,
)


class WorkflowResponse(BaseModel):
    """Public representation of a document workflow."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    current_status: WorkflowStatus
    priority: WorkflowPriority
    recommended_action: str | None
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime


class ApprovalDecisionRequest(BaseModel):
    """Decision submitted by an authorized workflow approver."""

    decision: ApprovalDecision
    comment: str | None = Field(default=None, max_length=5000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        """Remove extra spaces and treat blank comments as missing."""

        if value is None:
            return None

        return value.strip() or None

    @model_validator(mode="after")
    def validate_decision_comment(self):
        """Require an explanation for rejection or information requests."""

        if (
            self.decision
            in (
                ApprovalDecision.REJECTED,
                ApprovalDecision.INFORMATION_REQUESTED,
            )
            and not self.comment
        ):
            raise ValueError(
                "A comment is required when rejecting a document "
                "or requesting information."
            )

        return self


class ApprovalResponse(BaseModel):
    """Public representation of a recorded workflow approval."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    approver_id: int
    decision: ApprovalDecision
    comment: str | None
    created_at: datetime


class WorkflowDecisionResponse(BaseModel):
    """Result returned after a workflow approval decision."""

    workflow: WorkflowResponse
    approval: ApprovalResponse


class WorkflowReviewRequest(BaseModel):
    """Information submitted by a manager during manual review."""

    outcome: ReviewOutcome
    comment: str = Field(min_length=1)
    corrected_total_amount: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False,
    )


class WorkflowReviewResponse(BaseModel):
    """A recorded manual-review decision."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    reviewer_id: int
    outcome: ReviewOutcome
    comment: str
    created_at: datetime


class WorkflowReviewDecisionResponse(BaseModel):
    """Updated workflow and its newly recorded review."""

    workflow: WorkflowResponse
    review: WorkflowReviewResponse


class WorkflowInformationResponseRequest(BaseModel):
    """Information provided by an employee in response to a request."""

    response_comment: str = Field(
        min_length=1,
        max_length=5000,
    )

    @field_validator("response_comment")
    @classmethod
    def validate_response_comment(cls, value: str) -> str:
        """Reject empty messages and remove extra surrounding spaces."""

        clean_value = value.strip()

        if not clean_value:
            raise ValueError("An information response is required.")

        return clean_value


class WorkflowInformationRequestResponse(BaseModel):
    """Public representation of an information request and response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    approval_id: int | None
    review_id: int | None
    requested_by: int
    request_comment: str
    requested_at: datetime
    response_comment: str | None
    responded_by: int | None
    responded_at: datetime | None
    return_status: WorkflowStatus


class WorkflowInformationResponseDecisionResponse(BaseModel):
    """Result returned after an employee answers an information request."""

    workflow: WorkflowResponse
    information_request: WorkflowInformationRequestResponse


class WorkflowHistoryItemResponse(BaseModel):
    """Represent one approval or manual-review decision."""

    id: int
    action_type: str
    decided_by: int
    decision: str
    comment: str | None
    created_at: datetime


class WorkflowHistoryResponse(BaseModel):
    """Return the decision history for a workflow."""

    workflow_id: int
    history: list[WorkflowHistoryItemResponse]
