"""Regression tests for workflow authorization rules."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.db.enums import (
    ApprovalDecision,
    ReviewOutcome,
    UserRole,
    WorkflowStatus,
)
from app.security.document_access_policy import DocumentAccessPolicy
from app.services.workflow_service import WorkflowService


def make_user(user_id: int, role: UserRole):
    """Create a simple user for permission tests."""
    return SimpleNamespace(id=user_id, role=role)


def make_workflow(
    *,
    assigned_to: int | None,
    status: WorkflowStatus,
):
    """Create a workflow with a specific assignment."""
    return SimpleNamespace(
        id=10,
        assigned_to=assigned_to,
        current_status=status,
    )


@pytest.mark.parametrize(
    ("assigned_to", "expected"),
    [
        (None, True),
        (2, True),
        (3, False),
    ],
)
def test_manager_workflow_decision_permissions(
    assigned_to: int | None,
    expected: bool,
) -> None:
    """Managers can act only on assigned or shared work."""

    manager = make_user(2, UserRole.MANAGER)
    workflow = make_workflow(
        assigned_to=assigned_to,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    result = DocumentAccessPolicy.can_make_workflow_decision(
        workflow=workflow,
        current_user=manager,
    )

    assert result is expected


def test_admin_can_manage_assigned_workflow() -> None:
    """Admins can manage workflows assigned to other users."""

    admin = make_user(1, UserRole.ADMIN)
    workflow = make_workflow(
        assigned_to=3,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    assert DocumentAccessPolicy.can_make_workflow_decision(
        workflow=workflow,
        current_user=admin,
    )


def test_employee_cannot_make_workflow_decision() -> None:
    """Employees cannot approve or manually review workflows."""

    employee = make_user(4, UserRole.EMPLOYEE)
    workflow = make_workflow(
        assigned_to=None,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    assert not DocumentAccessPolicy.can_make_workflow_decision(
        workflow=workflow,
        current_user=employee,
    )


def test_other_manager_cannot_approve_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A denied approval must not create database records."""

    workflow = make_workflow(
        assigned_to=3,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    manager = make_user(2, UserRole.MANAGER)

    database_session = Mock()
    database_session.get.return_value = manager

    # Return the latest workflow during the locking step.
    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_for_update",
        Mock(return_value=workflow),
    )

    create_approval = Mock()

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        create_approval,
    )

    service = WorkflowService(database_session)
    service.audit_log_service.record_event = Mock()

    with pytest.raises(
        PermissionError,
        match="not allowed to make a decision",
    ):
        service.record_approval_decision(
            workflow=workflow,
            approver_id=manager.id,
            decision=ApprovalDecision.APPROVED,
        )

    # Nothing should be saved for an unauthorized decision.
    create_approval.assert_not_called()
    service.audit_log_service.record_event.assert_not_called()
    database_session.commit.assert_not_called()
    database_session.rollback.assert_called_once()


def test_other_manager_cannot_manually_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A denied manual review must not create a review record."""

    workflow = make_workflow(
        assigned_to=3,
        status=WorkflowStatus.NEEDS_REVIEW,
    )

    manager = make_user(2, UserRole.MANAGER)

    database_session = Mock()
    database_session.get.return_value = manager

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_for_update",
        Mock(return_value=workflow),
    )

    create_review = Mock()

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow_review",
        create_review,
    )

    service = WorkflowService(database_session)
    service.audit_log_service.record_event = Mock()

    with pytest.raises(
        PermissionError,
        match="not allowed to review",
    ):
        service.record_manual_review(
            workflow=workflow,
            reviewer_id=manager.id,
            outcome=ReviewOutcome.REJECTED,
            comment="Attempted unauthorized review.",
        )

    # The authorization check must stop the operation.
    create_review.assert_not_called()
    service.audit_log_service.record_event.assert_not_called()
    database_session.commit.assert_not_called()

    # The workflow status must remain unchanged.
    assert workflow.current_status == WorkflowStatus.NEEDS_REVIEW


@pytest.mark.parametrize(
    ("role", "user_id", "uploader_id", "assigned_to", "status", "expected"),
    [
        # Employees can see workflows for their own documents.
        (UserRole.EMPLOYEE, 2, 2, None, WorkflowStatus.COMPLETED, True),
        (UserRole.EMPLOYEE, 2, 3, None, WorkflowStatus.COMPLETED, False),
        # Managers can see workflows assigned to them.
        (UserRole.MANAGER, 2, 3, 2, WorkflowStatus.COMPLETED, True),
        # Managers cannot see other managers' assigned workflows.
        (UserRole.MANAGER, 2, 3, 4, WorkflowStatus.PENDING_APPROVAL, False),
        # Managers can see unassigned review-queue workflows.
        (UserRole.MANAGER, 2, 3, None, WorkflowStatus.NEEDS_REVIEW, True),
        (UserRole.MANAGER, 2, 3, None, WorkflowStatus.PENDING_APPROVAL, True),
        (UserRole.MANAGER, 2, 3, None, WorkflowStatus.NEEDS_INFORMATION, True),
        # Unassigned completed workflows are not visible to managers.
        (UserRole.MANAGER, 2, 3, None, WorkflowStatus.COMPLETED, False),
        # Admins can see workflows regardless of assignment.
        (UserRole.ADMIN, 1, 3, 4, WorkflowStatus.COMPLETED, True),
    ],
)
def test_workflow_visibility_permissions(
    role: UserRole,
    user_id: int,
    uploader_id: int,
    assigned_to: int | None,
    status: WorkflowStatus,
    expected: bool,
) -> None:
    """Check workflow visibility for employees, managers and admins."""

    current_user = make_user(user_id, role)

    # Simulate a document belonging to an employee.
    document = SimpleNamespace(uploaded_by=uploader_id)

    # Simulate a workflow linked to that document.
    workflow = SimpleNamespace(
        id=10,
        document=document,
        assigned_to=assigned_to,
        current_status=status,
    )

    result = DocumentAccessPolicy.can_view_workflow(
        workflow=workflow,
        current_user=current_user,
    )

    assert result is expected
