"""Integration tests for manual workflow review persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import (
    ReviewOutcome,
    UserRole,
    WorkflowStatus,
)
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow
from app.db.models.workflow_review import WorkflowReview
from app.repositories.workflow_review_repository import (
    create_workflow_review,
    get_reviews_by_workflow_id,
)


def create_review_test_records(
    db_session: Session,
) -> tuple[Workflow, User]:
    """Create the records required by a manual-review test."""

    # Create an employee who uploads the document.
    employee = User(
        name="Test Employee",
        email="review-employee@example.com",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
    )

    # Create a manager who reviews the document.
    manager = User(
        name="Test Manager",
        email="review-manager@example.com",
        password_hash="test-hash",
        role=UserRole.MANAGER,
    )

    db_session.add_all([employee, manager])
    db_session.flush()

    # Create a document owned by the employee.
    document = Document(
        uploaded_by=employee.id,
        original_file_name="review-test.txt",
        stored_file_name="review-test-stored.txt",
        file_path="uploads/review-test-stored.txt",
        mime_type="text/plain",
        file_size=100,
    )

    db_session.add(document)
    db_session.flush()

    # Create a workflow that needs manual review.
    workflow = Workflow(
        document_id=document.id,
        current_status=WorkflowStatus.NEEDS_REVIEW,
    )

    db_session.add(workflow)
    db_session.flush()

    return workflow, manager


def test_create_workflow_review(
    db_session: Session,
) -> None:
    """A manual-review decision is saved to the test database."""

    workflow, manager = create_review_test_records(db_session)

    review = create_workflow_review(
        database_session=db_session,
        workflow_id=workflow.id,
        reviewer_id=manager.id,
        outcome=ReviewOutcome.RESOLVED,
        comment="Verified the document details.",
    )

    # The database assigned a primary key during flush.
    assert review.id is not None

    stored_review = db_session.get(WorkflowReview, review.id)

    assert stored_review is not None
    assert stored_review.workflow_id == workflow.id
    assert stored_review.reviewer_id == manager.id
    assert stored_review.outcome == ReviewOutcome.RESOLVED
    assert stored_review.comment == "Verified the document details."
    assert stored_review.created_at is not None


def test_get_reviews_by_workflow_id(
    db_session: Session,
) -> None:
    """Review history is returned in creation order."""

    workflow, manager = create_review_test_records(db_session)

    create_workflow_review(
        database_session=db_session,
        workflow_id=workflow.id,
        reviewer_id=manager.id,
        outcome=ReviewOutcome.INFORMATION_REQUESTED,
        comment="Please provide the missing invoice details.",
    )

    create_workflow_review(
        database_session=db_session,
        workflow_id=workflow.id,
        reviewer_id=manager.id,
        outcome=ReviewOutcome.RESOLVED,
        comment="The required information was verified.",
    )

    reviews = get_reviews_by_workflow_id(
        database_session=db_session,
        workflow_id=workflow.id,
    )

    assert len(reviews) == 2
    assert reviews[0].outcome == ReviewOutcome.INFORMATION_REQUESTED
    assert reviews[1].outcome == ReviewOutcome.RESOLVED


def test_review_can_be_rolled_back(
    db_session: Session,
) -> None:
    """An uncommitted review can be rolled back."""

    workflow, manager = create_review_test_records(db_session)

    review = create_workflow_review(
        database_session=db_session,
        workflow_id=workflow.id,
        reviewer_id=manager.id,
        outcome=ReviewOutcome.REJECTED,
        comment="The submitted document is invalid.",
    )

    review_id = review.id

    # Undo the uncommitted INSERT.
    db_session.rollback()

    # The review should no longer exist.
    stored_review = db_session.scalar(
        select(WorkflowReview).where(
            WorkflowReview.id == review_id,
        )
    )

    assert stored_review is None


def test_reviews_for_unknown_workflow_return_empty(
    db_session: Session,
) -> None:
    """A workflow with no review records returns an empty list."""

    reviews = get_reviews_by_workflow_id(
        database_session=db_session,
        workflow_id=-1,
    )

    assert reviews == []
