"""
Business-rule engine for DocuFlow.

This module selects the appropriate deterministic rule evaluator
based on the analyzed document type.
"""

from app.business_rules.invoice_rules import evaluate_invoice_rules
from app.db.enums import DocumentType
from app.schemas.ai_schema import InvoiceExtraction
from app.schemas.business_rule_schema import (
    BusinessAction,
    BusinessRuleResult,
)


def evaluate_business_rules(
    document_type: DocumentType,
    extracted_data: InvoiceExtraction | None,
) -> BusinessRuleResult:
    """Evaluate business rules for an analyzed document."""

    if document_type == DocumentType.INVOICE:
        if extracted_data is None:
            raise ValueError("Invoice business rules require extracted invoice data.")

        return evaluate_invoice_rules(extracted_data)

    return BusinessRuleResult(
        requires_approval=False,
        approval_role=None,
        requires_manual_review=True,
        next_action=BusinessAction.MANUAL_REVIEW,
        reason=(
            "Business rules are not yet implemented for "
            f"document type: {document_type.value}."
        ),
    )
