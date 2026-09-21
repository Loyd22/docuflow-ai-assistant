"""
Deterministic business rules for invoices.

This module evaluates validated invoice extraction data and
returns a structured business decision without calling AI,
accessing the database, or handling HTTP concerns.
"""

from decimal import Decimal

from app.db.enums import UserRole
from app.schemas.ai_schema import InvoiceExtraction
from app.schemas.business_rule_schema import (
    BusinessAction,
    BusinessRuleResult,
)

MANAGER_APPROVAL_THRESHOLD = Decimal(20000)


def evaluate_invoice_rules(
    invoice: InvoiceExtraction,
) -> BusinessRuleResult:
    """Evaluate business rules for a validated invoice."""

    if invoice.total_amount is None:
        return BusinessRuleResult(
            requires_approval=False,
            approval_role=None,
            requires_manual_review=True,
            next_action=BusinessAction.MANUAL_REVIEW,
            reason="Invoice total is missing.",
        )

    total_amount = Decimal(str(invoice.total_amount))

    if total_amount > MANAGER_APPROVAL_THRESHOLD:
        return BusinessRuleResult(
            requires_approval=True,
            approval_role=UserRole.MANAGER,
            requires_manual_review=False,
            next_action=BusinessAction.MANAGER_REVIEW,
            reason="Invoice total exceeds the manager approval threshold.",
        )

    return BusinessRuleResult(
        requires_approval=False,
        approval_role=None,
        requires_manual_review=False,
        next_action=BusinessAction.CONTINUE_PROCESSING,
        reason="Invoice does not require manager approval.",
    )
