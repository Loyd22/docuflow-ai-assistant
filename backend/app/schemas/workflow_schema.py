"""
Pydantic schemas for workflow and approval operations.

These schemas define the data exposed through Phase 9 workflow
and approval API operations.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.enums import (
    ApprovalDecision,
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
    comment: str | None = None


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
