"""
Pydantic schemas for deterministic business-rule decisions.

These schemas define the validated contract returned by the
business-rules layer after evaluating structured document data.
"""

from enum import StrEnum

from pydantic import BaseModel

from app.db.enums import UserRole


class BusinessAction(StrEnum):
    """Actions that may result from business-rule evaluation."""

    CONTINUE_PROCESSING = "continue_processing"
    MANAGER_REVIEW = "manager_review"
    MANUAL_REVIEW = "manual_review"


class BusinessRuleResult(BaseModel):
    """Validated decision produced by the business-rules layer."""

    requires_approval: bool
    approval_role: UserRole | None = None

    requires_manual_review: bool

    next_action: BusinessAction
    reason: str
