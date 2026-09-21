"""
Unit tests for the DocuFlow business-rules engine.

These tests verify that the engine routes supported document types
to the correct deterministic rule evaluator and rejects unsupported
or incomplete inputs.
"""

import pytest

from app.business_rules.engine import evaluate_business_rules
from app.db.enums import DocumentType, UserRole
from app.schemas.ai_schema import InvoiceExtraction
from app.schemas.business_rule_schema import BusinessAction


def test_invoice_is_routed_to_invoice_rules() -> None:
    """Invoice documents should be evaluated using invoice rules."""

    invoice = InvoiceExtraction(
        invoice_number="INV-001",
        supplier="ABC Supplies",
        total_amount=25000.00,
    )

    result = evaluate_business_rules(
        document_type=DocumentType.INVOICE,
        extracted_data=invoice,
    )

    assert result.requires_approval is True
    assert result.approval_role == UserRole.MANAGER
    assert result.requires_manual_review is False
    assert result.next_action == BusinessAction.MANAGER_REVIEW


def test_invoice_without_extracted_data_is_rejected() -> None:
    """Invoice rules require validated invoice extraction data."""

    with pytest.raises(
        ValueError,
        match="Invoice business rules require extracted invoice data.",
    ):
        evaluate_business_rules(
            document_type=DocumentType.INVOICE,
            extracted_data=None,
        )


def test_unsupported_document_type_requires_manual_review() -> None:
    """Document types without rules should require manual review."""

    result = evaluate_business_rules(
        document_type=DocumentType.CONTRACT,
        extracted_data=None,
    )

    assert result.requires_approval is False
    assert result.approval_role is None
    assert result.requires_manual_review is True
    assert result.next_action == BusinessAction.MANUAL_REVIEW
    assert (
        result.reason
        == "Business rules are not yet implemented for document type: contract."
    )
