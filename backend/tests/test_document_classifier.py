from unittest.mock import Mock

import pytest

from app.ai.classifier import DocumentClassifier
from app.ai.exceptions import AIClassificationError
from app.db.enums import DocumentType
from app.schemas.ai_schema import DocumentClassification


def test_classifier_returns_valid_classification() -> None:
    """Classifier should return the parsed structured AI result."""

    expected_classification = DocumentClassification(
        document_type=DocumentType.INVOICE,
        confidence=0.98,
    )

    mock_response = Mock()
    mock_response.output_parsed = expected_classification

    mock_client = Mock()
    mock_client.responses.parse.return_value = mock_response

    classifier = DocumentClassifier(
        client=mock_client,
    )

    result = classifier.classify("Invoice Number: INV-001\nTotal Amount: PHP 10,000")

    assert result == expected_classification
    assert result.document_type == DocumentType.INVOICE
    assert result.confidence == 0.98


def test_classifier_rejects_empty_document_text() -> None:
    """Classifier should reject documents without usable text."""

    mock_client = Mock()

    classifier = DocumentClassifier(
        client=mock_client,
    )

    with pytest.raises(
        AIClassificationError,
        match="Document text cannot be empty",
    ):
        classifier.classify("   ")

    mock_client.responses.parse.assert_not_called()


def test_classifier_rejects_missing_parsed_result() -> None:
    """Classifier should reject responses without structured output."""

    mock_response = Mock()
    mock_response.output_parsed = None

    mock_client = Mock()
    mock_client.responses.parse.return_value = mock_response

    classifier = DocumentClassifier(
        client=mock_client,
    )

    with pytest.raises(
        AIClassificationError,
        match="valid document classification",
    ):
        classifier.classify("Invoice Number: INV-001")


def test_classifier_converts_provider_error() -> None:
    """Provider errors should become AIClassificationError."""

    mock_client = Mock()

    mock_client.responses.parse.side_effect = RuntimeError("Provider unavailable")

    classifier = DocumentClassifier(
        client=mock_client,
    )

    with pytest.raises(
        AIClassificationError,
        match="Document classification failed",
    ):
        classifier.classify("Invoice Number: INV-001")
