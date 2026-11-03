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


def test_classifier_converts_provider_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Convert provider failures without logging sensitive details."""

    sensitive_marker = "FAKE_SECRET_DO_NOT_LOG_123"

    mock_client = Mock()

    mock_client.responses.parse.side_effect = RuntimeError(
        f"Provider failed: authorization=Bearer {sensitive_marker}"
    )

    classifier = DocumentClassifier(client=mock_client)

    with pytest.raises(
        AIClassificationError,
        match="Document classification failed",
    ):
        classifier.classify("Invoice Number: INV-001")

    # Preserve a useful diagnostic message.
    assert "Document classification provider call failed." in caplog.text

    # Never log the original provider exception or its credentials.
    assert sensitive_marker not in caplog.text
    assert "authorization=Bearer" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)

    mock_client.responses.parse.assert_called_once()
