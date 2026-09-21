"""
Unit tests for deterministic invoice business rules.

These tests verify invoice rule behavior without requiring
FastAPI, PostgreSQL, OpenAI, or external services.
"""

from app.business_rules.invoice_rules import evaluate_invoice_rules
from app.db.enums import UserRole
from app.schemas.ai_schema import InvoiceExtraction
from app.schemas.business_rule_schema import BusinessAction


def test_missing_invoice_total_requires_manual_review() -> None:
    """Missing invoice totals should require manual review."""

    invoice = InvoiceExtraction(
        invoice_number="INV-001",
        supplier="ABC Supplies",
        total_amount=None,
    )

    result = evaluate_invoice_rules(invoice)

    assert result.requires_approval is False
    assert result.approval_role is None
    assert result.requires_manual_review is True
    assert result.next_action == BusinessAction.MANUAL_REVIEW
    assert result.reason == "Invoice total is missing."


def test_invoice_above_threshold_requires_manager_approval() -> None:
    """Invoices above the threshold should require manager approval."""

    invoice = InvoiceExtraction(
        invoice_number="INV-002",
        supplier="ABC Supplies",
        total_amount=20000.01,
    )

    result = evaluate_invoice_rules(invoice)

    assert result.requires_approval is True
    assert result.approval_role == UserRole.MANAGER
    assert result.requires_manual_review is False
    assert result.next_action == BusinessAction.MANAGER_REVIEW
    assert result.reason == "Invoice total exceeds the manager approval threshold."


def test_invoice_at_threshold_continues_processing() -> None:
    """An invoice exactly at the threshold should not require approval."""

    invoice = InvoiceExtraction(
        invoice_number="INV-003",
        supplier="ABC Supplies",
        total_amount=20000.00,
    )

    result = evaluate_invoice_rules(invoice)

    assert result.requires_approval is False
    assert result.approval_role is None
    assert result.requires_manual_review is False
    assert result.next_action == BusinessAction.CONTINUE_PROCESSING
    assert result.reason == "Invoice does not require manager approval."


def test_invoice_below_threshold_continues_processing() -> None:
    """An invoice below the threshold should continue processing."""

    invoice = InvoiceExtraction(
        invoice_number="INV-004",
        supplier="ABC Supplies",
        total_amount=15000.00,
    )

    result = evaluate_invoice_rules(invoice)

    assert result.requires_approval is False
    assert result.approval_role is None
    assert result.requires_manual_review is False
    assert result.next_action == BusinessAction.CONTINUE_PROCESSING
