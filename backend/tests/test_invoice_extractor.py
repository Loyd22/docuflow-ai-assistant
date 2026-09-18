from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.ai.exceptions import AIExtractionError
from app.ai.extractor import InvoiceExtractor
from app.schemas.ai_schema import InvoiceExtraction


def test_invoice_extractor_returns_valid_extraction() -> None:
    """Extractor should return parsed structured invoice data."""

    expected_extraction = InvoiceExtraction(
        invoice_number="INV-2026-001",
        supplier="ABC Office Supplies",
        invoice_date=date(2026, 9, 1),
        due_date=date(2026, 9, 30),
        currency="PHP",
        subtotal=Decimal("22000.00"),
        tax=Decimal("2640.00"),
        total_amount=Decimal("24640.00"),
    )

    mock_response = Mock()
    mock_response.output_parsed = expected_extraction

    mock_client = Mock()
    mock_client.responses.parse.return_value = mock_response

    extractor = InvoiceExtractor(
        client=mock_client,
    )

    result = extractor.extract(
        """
        ABC Office Supplies

        Invoice Number: INV-2026-001
        Invoice Date: September 1, 2026
        Due Date: September 30, 2026
        Subtotal: PHP 22,000
        Tax: PHP 2,640
        Total Amount: PHP 24,640
        """
    )

    assert result == expected_extraction
    assert result.invoice_number == "INV-2026-001"
    assert result.total_amount == Decimal("24640.00")


def test_invoice_extractor_rejects_empty_text() -> None:
    """Extractor should reject empty invoice text."""

    mock_client = Mock()

    extractor = InvoiceExtractor(
        client=mock_client,
    )

    with pytest.raises(
        AIExtractionError,
        match="Invoice text cannot be empty",
    ):
        extractor.extract("   ")

    mock_client.responses.parse.assert_not_called()


def test_invoice_extractor_rejects_missing_parsed_result() -> None:
    """Extractor should reject responses without structured data."""

    mock_response = Mock()
    mock_response.output_parsed = None

    mock_client = Mock()
    mock_client.responses.parse.return_value = mock_response

    extractor = InvoiceExtractor(
        client=mock_client,
    )

    with pytest.raises(
        AIExtractionError,
        match="valid invoice extraction data",
    ):
        extractor.extract("Invoice Number: INV-001")


def test_invoice_extractor_converts_provider_error() -> None:
    """Provider failures should become AIExtractionError."""

    mock_client = Mock()

    mock_client.responses.parse.side_effect = RuntimeError("Provider unavailable")

    extractor = InvoiceExtractor(
        client=mock_client,
    )

    with pytest.raises(
        AIExtractionError,
        match="Invoice extraction failed",
    ):
        extractor.extract("Invoice Number: INV-001")


def test_invoice_extractor_allows_missing_optional_fields() -> None:
    """Missing invoice fields should remain None instead of being invented."""

    expected_extraction = InvoiceExtraction(
        invoice_number="INV-001",
        supplier="ABC Corporation",
        total_amount=Decimal("5000.00"),
    )

    mock_response = Mock()
    mock_response.output_parsed = expected_extraction

    mock_client = Mock()
    mock_client.responses.parse.return_value = mock_response

    extractor = InvoiceExtractor(
        client=mock_client,
    )

    result = extractor.extract(
        """
        Invoice Number: INV-001
        Supplier: ABC Corporation
        Total Amount: PHP 5,000
        """
    )

    assert result.invoice_date is None
    assert result.due_date is None
    assert result.subtotal is None
    assert result.tax is None
