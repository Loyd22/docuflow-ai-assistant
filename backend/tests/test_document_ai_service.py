from decimal import Decimal
from unittest.mock import Mock

from app.db.enums import DocumentType
from app.schemas.ai_schema import (
    DocumentClassification,
    InvoiceExtraction,
)
from app.services.document_ai_service import DocumentAIService


def test_ai_service_classifies_and_extracts_invoice() -> None:
    """Invoice documents should be classified and extracted."""

    classification = DocumentClassification(
        document_type=DocumentType.INVOICE,
        confidence=0.98,
    )

    extraction = InvoiceExtraction(
        invoice_number="INV-001",
        supplier="ABC Corporation",
        currency="PHP",
        total_amount=Decimal("25000.00"),
    )

    mock_classifier = Mock()
    mock_classifier.classify.return_value = classification

    mock_invoice_extractor = Mock()
    mock_invoice_extractor.extract.return_value = extraction

    service = DocumentAIService(
        classifier=mock_classifier,
        invoice_extractor=mock_invoice_extractor,
    )

    document_text = """
    Invoice Number: INV-001
    Supplier: ABC Corporation
    Total Amount: PHP 25,000
    """

    result = service.analyze_document(document_text)

    assert result.classification == classification
    assert result.extracted_data == extraction

    mock_classifier.classify.assert_called_once_with(document_text)

    mock_invoice_extractor.extract.assert_called_once_with(document_text)


def test_ai_service_does_not_extract_unsupported_document_type() -> None:
    """Unsupported extraction types should return no extracted data."""

    classification = DocumentClassification(
        document_type=DocumentType.CONTRACT,
        confidence=0.95,
    )

    mock_classifier = Mock()
    mock_classifier.classify.return_value = classification

    mock_invoice_extractor = Mock()

    service = DocumentAIService(
        classifier=mock_classifier,
        invoice_extractor=mock_invoice_extractor,
    )

    document_text = """
    This agreement is entered into between Company A and Company B.
    """

    result = service.analyze_document(document_text)

    assert result.classification == classification
    assert result.extracted_data is None

    mock_invoice_extractor.extract.assert_not_called()


def test_ai_service_handles_unknown_document_type() -> None:
    """Unknown documents should not trigger structured extraction."""

    classification = DocumentClassification(
        document_type=DocumentType.UNKNOWN,
        confidence=0.85,
    )

    mock_classifier = Mock()
    mock_classifier.classify.return_value = classification

    mock_invoice_extractor = Mock()

    service = DocumentAIService(
        classifier=mock_classifier,
        invoice_extractor=mock_invoice_extractor,
    )

    result = service.analyze_document(
        "Random content that does not match a supported document type."
    )

    assert result.classification.document_type == DocumentType.UNKNOWN
    assert result.extracted_data is None

    mock_invoice_extractor.extract.assert_not_called()
