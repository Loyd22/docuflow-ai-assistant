"""
Unit tests for the persistent document AI analysis workflow.

These tests verify that DocumentAnalysisService correctly coordinates:
- document readiness validation
- AI analysis
- business-rule evaluation
- AI result persistence
- business-rule result persistence
- workflow creation
- document status transitions
- AI failure handling

External AI calls, workflow operations, and repository operations are
mocked so these tests remain fast and deterministic.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.ai.exceptions import AIClassificationError, AIExtractionError
from app.db.enums import DocumentStatus, DocumentType, UserRole
from app.schemas.ai_schema import (
    DocumentAnalysisResult,
    DocumentClassification,
    InvoiceExtraction,
)
from app.schemas.business_rule_schema import BusinessAction
from app.services.document_analysis_service import DocumentAnalysisService


def test_analysis_service_persists_successful_invoice_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful invoice analysis should persist AI, rules, and workflow."""

    document = Mock()
    document.status = DocumentStatus.TEXT_EXTRACTED
    document.extracted_text = """
    Invoice Number: INV-001
    Supplier: ABC Corporation
    Total Amount: PHP 25,000
    """

    analysis_result = DocumentAnalysisResult(
        classification=DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.98,
        ),
        extracted_data=InvoiceExtraction(
            invoice_number="INV-001",
            supplier="ABC Corporation",
            currency="PHP",
            total_amount=Decimal("25000.00"),
        ),
    )

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.return_value = analysis_result

    mock_workflow_service = Mock()

    mock_update_status = Mock()
    mock_update_ai_analysis = Mock()
    mock_update_business_rule_result = Mock()

    monkeypatch.setattr(
        "app.services.document_analysis_service.update_document_status",
        mock_update_status,
    )

    monkeypatch.setattr(
        "app.services.document_analysis_service.update_ai_analysis",
        mock_update_ai_analysis,
    )

    monkeypatch.setattr(
        "app.services.document_analysis_service.update_business_rule_result",
        mock_update_business_rule_result,
    )

    mock_database_session = Mock()

    service = DocumentAnalysisService(
        database_session=mock_database_session,
        ai_service=mock_ai_service,
        workflow_service=mock_workflow_service,
    )

    analyzed_document, business_rule_result = service.analyze(document)

    assert analyzed_document is document

    mock_ai_service.analyze_document.assert_called_once_with(document.extracted_text)

    assert mock_update_status.call_count == 2

    first_status_call = mock_update_status.call_args_list[0]
    assert first_status_call.kwargs["status"] == DocumentStatus.AI_PROCESSING

    second_status_call = mock_update_status.call_args_list[1]
    assert second_status_call.kwargs["status"] == DocumentStatus.ANALYZED

    mock_update_ai_analysis.assert_called_once()

    persistence_call = mock_update_ai_analysis.call_args

    assert persistence_call.kwargs["document_type"] == DocumentType.INVOICE
    assert persistence_call.kwargs["classification_confidence"] == 0.98

    extracted_data = persistence_call.kwargs["extracted_data"]

    assert extracted_data["invoice_number"] == "INV-001"
    assert extracted_data["supplier"] == "ABC Corporation"
    assert extracted_data["currency"] == "PHP"

    assert business_rule_result.requires_approval is True
    assert business_rule_result.approval_role == UserRole.MANAGER
    assert business_rule_result.requires_manual_review is False
    assert business_rule_result.next_action == BusinessAction.MANAGER_REVIEW

    mock_update_business_rule_result.assert_called_once_with(
        database_session=mock_database_session,
        document=document,
        business_rule_result={
            "requires_approval": True,
            "approval_role": "manager",
            "requires_manual_review": False,
            "next_action": "manager_review",
            "reason": "Invoice total exceeds the manager approval threshold.",
        },
    )

    mock_workflow_service.create_from_business_rule.assert_called_once_with(
        document=document,
        business_rule_result=business_rule_result,
    )


def test_analysis_service_rejects_document_not_ready() -> None:
    """Documents that have not completed text extraction should be rejected."""

    document = Mock()
    document.status = DocumentStatus.UPLOADED
    document.extracted_text = None

    mock_ai_service = Mock()
    mock_workflow_service = Mock()
    mock_database_session = Mock()

    service = DocumentAnalysisService(
        database_session=mock_database_session,
        ai_service=mock_ai_service,
        workflow_service=mock_workflow_service,
    )

    with pytest.raises(
        ValueError,
        match="Document is not ready for AI analysis",
    ):
        service.analyze(document)

    mock_ai_service.analyze_document.assert_not_called()
    mock_workflow_service.create_from_business_rule.assert_not_called()


def test_analysis_service_rejects_missing_extracted_text() -> None:
    """A text-extracted document must actually contain extracted text."""

    document = Mock()
    document.status = DocumentStatus.TEXT_EXTRACTED
    document.extracted_text = None

    mock_ai_service = Mock()
    mock_workflow_service = Mock()
    mock_database_session = Mock()

    service = DocumentAnalysisService(
        database_session=mock_database_session,
        ai_service=mock_ai_service,
        workflow_service=mock_workflow_service,
    )

    with pytest.raises(
        ValueError,
        match="Document does not contain extracted text",
    ):
        service.analyze(document)

    mock_ai_service.analyze_document.assert_not_called()
    mock_workflow_service.create_from_business_rule.assert_not_called()


def test_analysis_service_marks_failed_on_classification_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Classification failures should mark AI processing as failed."""

    document = Mock()
    document.status = DocumentStatus.TEXT_EXTRACTED
    document.extracted_text = "Some document text."

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.side_effect = AIClassificationError(
        "Document classification failed."
    )

    mock_workflow_service = Mock()
    mock_update_status = Mock()

    monkeypatch.setattr(
        "app.services.document_analysis_service.update_document_status",
        mock_update_status,
    )

    mock_database_session = Mock()

    service = DocumentAnalysisService(
        database_session=mock_database_session,
        ai_service=mock_ai_service,
        workflow_service=mock_workflow_service,
    )

    with pytest.raises(AIClassificationError):
        service.analyze(document)

    assert mock_update_status.call_count == 2

    first_status_call = mock_update_status.call_args_list[0]
    assert first_status_call.kwargs["status"] == DocumentStatus.AI_PROCESSING

    second_status_call = mock_update_status.call_args_list[1]
    assert second_status_call.kwargs["status"] == DocumentStatus.AI_PROCESSING_FAILED

    mock_workflow_service.create_from_business_rule.assert_not_called()


def test_analysis_service_marks_failed_on_extraction_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extraction failures should mark AI processing as failed."""

    document = Mock()
    document.status = DocumentStatus.TEXT_EXTRACTED
    document.extracted_text = """
    Invoice Number: INV-001
    Total Amount: PHP 25,000
    """

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.side_effect = AIExtractionError(
        "Invoice extraction failed."
    )

    mock_workflow_service = Mock()
    mock_update_status = Mock()

    monkeypatch.setattr(
        "app.services.document_analysis_service.update_document_status",
        mock_update_status,
    )

    mock_database_session = Mock()

    service = DocumentAnalysisService(
        database_session=mock_database_session,
        ai_service=mock_ai_service,
        workflow_service=mock_workflow_service,
    )

    with pytest.raises(AIExtractionError):
        service.analyze(document)

    assert mock_update_status.call_count == 2

    first_status_call = mock_update_status.call_args_list[0]
    assert first_status_call.kwargs["status"] == DocumentStatus.AI_PROCESSING

    second_status_call = mock_update_status.call_args_list[1]
    assert second_status_call.kwargs["status"] == DocumentStatus.AI_PROCESSING_FAILED

    mock_workflow_service.create_from_business_rule.assert_not_called()
