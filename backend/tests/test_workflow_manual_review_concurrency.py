"""Test concurrent manual-review decisions using PostgreSQL row locks."""

from threading import Event, Thread
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
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
from app.repositories.workflow_repository import get_workflow_for_update
from app.services.workflow_service import (
    InvalidWorkflowStateError,
    WorkflowService,
)


def test_concurrent_manual_reviews() -> None:
    """Only the first manager can complete a pending manual review."""

    # Both sessions connect to the test database, not development.
    engine = create_engine(settings.test_database_url)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    unique_id = uuid4().hex
    started = Event()
    finished = Event()
    errors: list[Exception] = []

    employee_id = None
    manager_id = None
    document_id = None
    workflow_id = None

    try:
        # Commit baseline records so both connections can see them.
        with SessionLocal() as session:
            employee = User(
                name="Concurrency Employee",
                email=f"employee-{unique_id}@example.com",
                password_hash="test-hash",
                role=UserRole.EMPLOYEE,
            )
            manager = User(
                name="Concurrency Manager",
                email=f"manager-{unique_id}@example.com",
                password_hash="test-hash",
                role=UserRole.MANAGER,
            )
            session.add_all([employee, manager])
            session.flush()

            document = Document(
                uploaded_by=employee.id,
                original_file_name="concurrent-invoice.txt",
                stored_file_name=f"{unique_id}.txt",
                file_path=f"uploads/{unique_id}.txt",
                mime_type="text/plain",
                file_size=100,
                document_type=DocumentType.INVOICE,
                extracted_data={"total_amount": None},
            )
            session.add(document)
            session.flush()

            workflow = Workflow(
                document_id=document.id,
                current_status=WorkflowStatus.NEEDS_REVIEW,
            )
            session.add(workflow)
            session.flush()

            employee_id = employee.id
            manager_id = manager.id
            document_id = document.id
            workflow_id = workflow.id

            session.commit()

        def manager_b() -> None:
            """Attempt a conflicting review from another connection."""

            try:
                with SessionLocal() as session:
                    # Prevent an unexpected database lock from hanging.
                    session.execute(text("SET LOCAL lock_timeout = '5s'"))

                    service = WorkflowService(
                        database_session=session,
                    )
                    workflow = session.get(Workflow, workflow_id)

                    started.set()

                    service.record_manual_review(
                        workflow=workflow,
                        reviewer_id=manager_id,
                        outcome=ReviewOutcome.REJECTED,
                        comment="Manager B rejects the invoice.",
                    )

            except Exception as exc:  # noqa: BLE001
                # Save thread errors so the main test can report them.
                errors.append(exc)
            finally:
                finished.set()

        with SessionLocal() as session_a:
            # Manager A obtains the PostgreSQL row lock first.
            locked_workflow = get_workflow_for_update(
                database_session=session_a,
                workflow_id=workflow_id,
            )

            assert locked_workflow is not None

            worker = Thread(target=manager_b, daemon=True)
            worker.start()

            assert started.wait(timeout=3)

            # Manager B must not finish while A holds the lock.
            assert not finished.wait(timeout=0.3)

            # Manager A completes the workflow and releases the lock.
            service_a = WorkflowService(
                database_session=session_a,
            )
            service_a.record_manual_review(
                workflow=locked_workflow,
                reviewer_id=manager_id,
                outcome=ReviewOutcome.RESOLVED,
                comment="Manager A verified the invoice.",
                corrected_total_amount=5000.0,
            )

        worker.join(timeout=8)

        assert not worker.is_alive()
        assert len(errors) == 1
        assert isinstance(errors[0], InvalidWorkflowStateError)

        # Confirm only Manager A's decision was saved.
        with SessionLocal() as session:
            workflow = session.get(Workflow, workflow_id)
            assert workflow.current_status == WorkflowStatus.COMPLETED

            review_count = session.scalar(
                select(func.count(WorkflowReview.id)).where(
                    WorkflowReview.workflow_id == workflow_id
                )
            )
            assert review_count == 1

            audit_count = session.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.entity_type == AuditEntityType.WORKFLOW,
                    AuditLog.entity_id == workflow_id,
                    AuditLog.action == AuditAction.WORKFLOW_REVIEW_RESOLVED,
                )
            )
            assert audit_count == 1

    finally:
        # Allow blocked connections to finish before cleanup.
        if "worker" in locals() and worker.is_alive():
            worker.join(timeout=8)

        if "worker" not in locals() or not worker.is_alive():
            # Remove only records created by this test.
            with SessionLocal() as session:
                if workflow_id is not None:
                    session.execute(
                        delete(AuditLog).where(
                            AuditLog.entity_type == AuditEntityType.WORKFLOW,
                            AuditLog.entity_id == workflow_id,
                        )
                    )
                    session.execute(
                        delete(WorkflowReview).where(
                            WorkflowReview.workflow_id == workflow_id
                        )
                    )
                    session.execute(delete(Workflow).where(Workflow.id == workflow_id))

                if document_id is not None:
                    session.execute(delete(Document).where(Document.id == document_id))

                if employee_id is not None and manager_id is not None:
                    session.execute(
                        delete(User).where(User.id.in_([employee_id, manager_id]))
                    )

                session.commit()

        engine.dispose()
