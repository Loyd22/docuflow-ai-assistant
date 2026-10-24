"""Integration tests for manual-review workflow decisions."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import (
    AuditAction,
    AuditEntityType,
    DocumentType,
    ReviewOutcome,
    UserRole,
    WorkflowStatus,
)
from app.db.models.audit_log import AuditLog
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow
from app.db.models.workflow_review import WorkflowReview
from app.services.workflow_service import (
    InvalidWorkflowStateError,
    WorkflowService,
)


@pytest.fixture()
def review_records(
    db_session: Session,
) -> tuple[Workflow, User]:
    """Create an invoice workflow and a manager for each test."""

    employee = User(
        name="Review Test Employee",
        email="manual-review-employee@example.com",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
    )
    manager = User(
        name="Review Test Manager",
        email="manual-review-manager@example.com",
        password_hash="test-hash",
        role=UserRole.MANAGER,
    )

    db_session.add_all([employee, manager])
    db_session.flush()

    document = Document(
        uploaded_by=employee.id,
        original_file_name="invoice.txt",
        stored_file_name="manual-review-invoice.txt",
        file_path="uploads/manual-review-invoice.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.INVOICE,
        extracted_data={
            "invoice_number": "INV-001",
            "supplier": "Test Supplier",
            "total_amount": None,
        },
    )

    db_session.add(document)
    db_session.flush()

    workflow = Workflow(
        document_id=document.id,
        current_status=WorkflowStatus.NEEDS_REVIEW,
    )

    db_session.add(workflow)

    # Save the initial test records before testing service rollback.
    db_session.commit()

    return workflow, manager


@pytest.mark.parametrize(
    ("amount", "expected_status"),
    [
        (5000.0, WorkflowStatus.COMPLETED),
        (20000.0, WorkflowStatus.COMPLETED),
        (25000.0, WorkflowStatus.PENDING_APPROVAL),
    ],
)
def test_resolved_invoice_rechecks_business_rules(
    db_session: Session,
    review_records: tuple[Workflow, User],
    amount: float,
    expected_status: WorkflowStatus,
) -> None:
    """Corrected invoices follow the existing approval threshold."""

    workflow, manager = review_records

    service = WorkflowService(database_session=db_session)

    updated_workflow, review = service.record_manual_review(
        workflow=workflow,
        reviewer_id=manager.id,
        outcome=ReviewOutcome.RESOLVED,
        comment="Verified the amount against the invoice.",
        corrected_total_amount=amount,
    )

    assert updated_workflow.current_status == expected_status
    assert review.outcome == ReviewOutcome.RESOLVED
    assert review.reviewer_id == manager.id

    # Confirm the corrected invoice fields were saved.
    db_session.refresh(workflow.document)

    assert workflow.document.extracted_data["total_amount"] == amount
    assert workflow.document.extracted_data["invoice_number"] == "INV-001"

    rule_result = workflow.document.business_rule_result

    if expected_status == WorkflowStatus.PENDING_APPROVAL:
        assert rule_result["next_action"] == "manager_review"
    else:
        assert rule_result["next_action"] == "continue_processing"

    # Confirm the decision exists in the database.
    stored_review = db_session.get(WorkflowReview, review.id)
    assert stored_review is not None

    audit_log = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == AuditEntityType.WORKFLOW,
            AuditLog.entity_id == workflow.id,
            AuditLog.action == AuditAction.WORKFLOW_REVIEW_RESOLVED,
        )
    )

    assert audit_log is not None
    assert audit_log.event_metadata["review_id"] == review.id
    assert audit_log.event_metadata["corrected_total_amount"] == amount


@pytest.mark.parametrize(
    ("outcome", "expected_status", "expected_action"),
    [
        (
            ReviewOutcome.REJECTED,
            WorkflowStatus.REJECTED,
            AuditAction.WORKFLOW_REVIEW_REJECTED,
        ),
        (
            ReviewOutcome.INFORMATION_REQUESTED,
            WorkflowStatus.NEEDS_INFORMATION,
            AuditAction.WORKFLOW_REVIEW_INFORMATION_REQUESTED,
        ),
    ],
)
def test_other_review_outcomes(
    db_session: Session,
    review_records: tuple[Workflow, User],
    outcome: ReviewOutcome,
    expected_status: WorkflowStatus,
    expected_action: AuditAction,
) -> None:
    """Rejection and information requests update the workflow."""

    workflow, manager = review_records

    service = WorkflowService(database_session=db_session)

    updated_workflow, review = service.record_manual_review(
        workflow=workflow,
        reviewer_id=manager.id,
        outcome=outcome,
        comment="Manager decision recorded.",
    )

    assert updated_workflow.current_status == expected_status
    assert review.outcome == outcome

    audit_log = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == workflow.id,
            AuditLog.action == expected_action,
        )
    )

    assert audit_log is not None
    assert workflow.document.extracted_data["total_amount"] is None


@pytest.mark.parametrize(
    ("comment", "amount", "error_message"),
    [
        ("   ", 5000.0, "comment is required"),
        ("Verified.", None, "total is required"),
        ("Verified.", -100.0, "nonnegative"),
    ],
)
def test_invalid_review_input(
    db_session: Session,
    review_records: tuple[Workflow, User],
    comment: str,
    amount: float | None,
    error_message: str,
) -> None:
    """Invalid review inputs must not create a decision."""

    workflow, manager = review_records

    service = WorkflowService(database_session=db_session)

    with pytest.raises(ValueError, match=error_message):
        service.record_manual_review(
            workflow=workflow,
            reviewer_id=manager.id,
            outcome=ReviewOutcome.RESOLVED,
            comment=comment,
            corrected_total_amount=amount,
        )

    reviews = db_session.scalars(
        select(WorkflowReview).where(
            WorkflowReview.workflow_id == workflow.id,
        )
    ).all()

    assert reviews == []
    assert workflow.current_status == WorkflowStatus.NEEDS_REVIEW


def test_cannot_review_completed_workflow(
    db_session: Session,
    review_records: tuple[Workflow, User],
) -> None:
    """Only needs-review workflows can receive manual decisions."""

    workflow, manager = review_records

    # Save the completed status to PostgreSQL.
    workflow.current_status = WorkflowStatus.COMPLETED
    db_session.commit()

    service = WorkflowService(database_session=db_session)

    with pytest.raises(
        InvalidWorkflowStateError,
        match="not waiting for manual review",
    ):
        service.record_manual_review(
            workflow=workflow,
            reviewer_id=manager.id,
            outcome=ReviewOutcome.REJECTED,
            comment="Trying to review a completed workflow.",
        )

    # Verify that the rejected decision was not recorded.
    reviews = db_session.scalars(
        select(WorkflowReview).where(
            WorkflowReview.workflow_id == workflow.id,
        )
    ).all()

    assert reviews == []
    assert workflow.current_status == WorkflowStatus.COMPLETED


def test_failed_audit_rolls_back_review_and_correction(
    db_session: Session,
    review_records: tuple[Workflow, User],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If audit recording fails, none of the changes persist."""

    workflow, manager = review_records
    workflow_id = workflow.id
    document_id = workflow.document_id

    service = WorkflowService(database_session=db_session)

    def fail_audit(**kwargs: object) -> None:
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        service.audit_log_service,
        "record_event",
        fail_audit,
    )

    with pytest.raises(RuntimeError, match="Simulated audit failure"):
        service.record_manual_review(
            workflow=workflow,
            reviewer_id=manager.id,
            outcome=ReviewOutcome.RESOLVED,
            comment="Verified the corrected invoice.",
            corrected_total_amount=25000.0,
        )

    # Read the records again after the service rollback.
    persisted_workflow = db_session.get(Workflow, workflow_id)
    persisted_document = db_session.get(Document, document_id)

    assert persisted_workflow.current_status == WorkflowStatus.NEEDS_REVIEW
    assert persisted_document.extracted_data["total_amount"] is None

    reviews = db_session.scalars(
        select(WorkflowReview).where(
            WorkflowReview.workflow_id == workflow_id,
        )
    ).all()

    assert reviews == []
