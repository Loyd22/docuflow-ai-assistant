"""
Integration tests for persistent document analysis.

These tests verify that DocumentAnalysisService, business rules,
repositories, SQLAlchemy, and PostgreSQL work together correctly.

The AI service is mocked so the test remains deterministic and
does not make external provider requests.
"""

from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus, DocumentType, UserRole
from app.db.models.document import Document
from app.db.models.user import User
from app.schemas.ai_schema import (
    DocumentAnalysisResult,
    DocumentClassification,
    InvoiceExtraction,
)
from app.schemas.business_rule_schema import BusinessAction
from app.services.document_analysis_service import DocumentAnalysisService


def test_invoice_analysis_persists_business_rule_result(
    db_session: Session,
) -> None:
    """Invoice analysis should persist AI and business-rule results."""

    # Create a real user because Document.uploaded_by
    # has a foreign-key relationship to users.id.
    user = User(
        name="Integration Test User",
        email="analysis-integration@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create a real document that is already ready for AI analysis.
    document = Document(
        uploaded_by=user.id,
        original_file_name="invoice.txt",
        stored_file_name="integration-test-invoice.txt",
        file_path="uploads/integration-test-invoice.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="""
        Invoice Number: INV-001
        Supplier: ABC Corporation
        Currency: PHP
        Total Amount: 25000.00
        """,
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    # Mock only the AI boundary.
    # Everything after this result is real application code.
    analysis_result = DocumentAnalysisResult(
        classification=DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.98,
        ),
        extracted_data=InvoiceExtraction(
            invoice_number="INV-001",
            supplier="ABC Corporation",
            currency="PHP",
            total_amount=25000.00,
        ),
    )

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.return_value = analysis_result

    service = DocumentAnalysisService(
        database_session=db_session,
        ai_service=mock_ai_service,
    )

    analyzed_document, business_rule_result = service.analyze(document)

    # Verify the returned Phase 8 decision.
    assert business_rule_result.requires_approval is True
    assert business_rule_result.approval_role == UserRole.MANAGER
    assert business_rule_result.requires_manual_review is False
    assert business_rule_result.next_action == BusinessAction.MANAGER_REVIEW

    # Clear SQLAlchemy's cached object state so the following
    # lookup reloads persisted values from PostgreSQL.
    db_session.expire_all()

    persisted_document = db_session.get(
        Document,
        analyzed_document.id,
    )

    assert persisted_document is not None

    # Verify Phase 7 persistence.
    assert persisted_document.document_type == DocumentType.INVOICE
    assert persisted_document.classification_confidence == 0.98
    assert persisted_document.status == DocumentStatus.ANALYZED

    assert persisted_document.extracted_data is not None
    assert persisted_document.extracted_data["invoice_number"] == "INV-001"
    assert persisted_document.extracted_data["supplier"] == "ABC Corporation"
    assert persisted_document.extracted_data["currency"] == "PHP"
    assert persisted_document.extracted_data["total_amount"] == 25000.00

    # Verify Phase 8 persistence.
    assert persisted_document.business_rule_result is not None

    assert persisted_document.business_rule_result["requires_approval"] is True
    assert persisted_document.business_rule_result["approval_role"] == "manager"
    assert persisted_document.business_rule_result["requires_manual_review"] is False
    assert persisted_document.business_rule_result["next_action"] == "manager_review"
    assert (
        persisted_document.business_rule_result["reason"]
        == "Invoice total exceeds the manager approval threshold."
    )


def test_invoice_with_missing_total_requires_manual_review(
    db_session: Session,
) -> None:
    """Missing invoice total should persist a manual-review decision."""

    user = User(
        name="Missing Total User",
        email="missing-total@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    document = Document(
        uploaded_by=user.id,
        original_file_name="invoice.txt",
        stored_file_name="missing-total-invoice.txt",
        file_path="uploads/missing-total-invoice.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="Invoice Number: INV-002",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    analysis_result = DocumentAnalysisResult(
        classification=DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.95,
        ),
        extracted_data=InvoiceExtraction(
            invoice_number="INV-002",
            supplier="ABC Corporation",
            total_amount=None,
        ),
    )

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.return_value = analysis_result

    service = DocumentAnalysisService(
        database_session=db_session,
        ai_service=mock_ai_service,
    )

    service.analyze(document)

    db_session.expire_all()

    persisted_document = db_session.get(Document, document.id)

    assert persisted_document is not None
    assert persisted_document.business_rule_result is not None
    assert persisted_document.business_rule_result["requires_approval"] is False
    assert persisted_document.business_rule_result["requires_manual_review"] is True
    assert persisted_document.business_rule_result["next_action"] == "manual_review"


def test_invoice_below_threshold_continues_processing(
    db_session: Session,
) -> None:
    """Invoice below approval threshold should continue processing."""

    user = User(
        name="Normal Invoice User",
        email="normal-invoice@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    document = Document(
        uploaded_by=user.id,
        original_file_name="invoice.txt",
        stored_file_name="normal-invoice.txt",
        file_path="uploads/normal-invoice.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="Total Amount: 15000.00",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    analysis_result = DocumentAnalysisResult(
        classification=DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.97,
        ),
        extracted_data=InvoiceExtraction(
            invoice_number="INV-003",
            supplier="ABC Corporation",
            total_amount=15000.00,
        ),
    )

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.return_value = analysis_result

    service = DocumentAnalysisService(
        database_session=db_session,
        ai_service=mock_ai_service,
    )

    service.analyze(document)

    db_session.expire_all()

    persisted_document = db_session.get(Document, document.id)

    assert persisted_document is not None
    assert persisted_document.business_rule_result is not None
    assert persisted_document.business_rule_result["requires_approval"] is False
    assert persisted_document.business_rule_result["requires_manual_review"] is False
    assert (
        persisted_document.business_rule_result["next_action"] == "continue_processing"
    )


def test_unsupported_document_type_requires_manual_review(
    db_session: Session,
) -> None:
    """Unsupported business-rule types should persist manual review."""

    user = User(
        name="Contract Review User",
        email="contract-review@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    document = Document(
        uploaded_by=user.id,
        original_file_name="contract.txt",
        stored_file_name="contract-review.txt",
        file_path="uploads/contract-review.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="Contract between Company A and Company B.",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    analysis_result = DocumentAnalysisResult(
        classification=DocumentClassification(
            document_type=DocumentType.CONTRACT,
            confidence=0.96,
        ),
        extracted_data=None,
    )

    mock_ai_service = Mock()
    mock_ai_service.analyze_document.return_value = analysis_result

    service = DocumentAnalysisService(
        database_session=db_session,
        ai_service=mock_ai_service,
    )

    service.analyze(document)

    db_session.expire_all()

    persisted_document = db_session.get(Document, document.id)

    assert persisted_document is not None
    assert persisted_document.business_rule_result is not None
    assert persisted_document.business_rule_result["requires_approval"] is False
    assert persisted_document.business_rule_result["requires_manual_review"] is True
    assert persisted_document.business_rule_result["next_action"] == "manual_review"
