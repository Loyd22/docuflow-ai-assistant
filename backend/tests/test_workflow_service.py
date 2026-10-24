"""
Unit tests for the workflow and approval service.

These tests verify that WorkflowService correctly:
- converts Phase 8 business-rule decisions into workflow states
- prevents duplicate workflows
- records approval decisions
- updates workflow status after approval decisions
- rejects decisions for workflows that are not pending approval
- records important workflow actions in the audit log

Repository operations are mocked so these tests remain fast
and deterministic.
"""

from unittest.mock import Mock

import pytest

from app.db.enums import (
    ApprovalDecision,
    AuditAction,
    AuditEntityType,
    UserRole,
    WorkflowStatus,
)
from app.db.models.user import User
from app.schemas.business_rule_schema import (
    BusinessAction,
    BusinessRuleResult,
)
from app.services.workflow_service import (
    InvalidWorkflowStateError,
    WorkflowAlreadyExistsError,
    WorkflowService,
)


def test_create_manager_review_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manager review should create a pending-approval workflow."""

    document = Mock()
    document.id = 10

    business_rule_result = BusinessRuleResult(
        requires_approval=True,
        approval_role=UserRole.MANAGER,
        requires_manual_review=False,
        next_action=BusinessAction.MANAGER_REVIEW,
        reason="Manager approval is required.",
    )

    mock_get_workflow = Mock(return_value=None)

    created_workflow = Mock()
    created_workflow.id = 20
    created_workflow.current_status = WorkflowStatus.PENDING_APPROVAL

    mock_create_workflow = Mock(return_value=created_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_by_document_id",
        mock_get_workflow,
    )

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    mock_database_session = Mock()

    service = WorkflowService(
        database_session=mock_database_session,
    )

    mock_record_event = Mock()
    service.audit_log_service.record_event = mock_record_event

    workflow = service.create_from_business_rule(
        document=document,
        business_rule_result=business_rule_result,
    )

    assert workflow is created_workflow

    mock_create_workflow.assert_called_once_with(
        database_session=mock_database_session,
        document_id=10,
        current_status=WorkflowStatus.PENDING_APPROVAL,
        recommended_action="manager_review",
    )

    mock_record_event.assert_called_once_with(
        user_id=None,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=20,
        event_metadata={
            "document_id": 10,
            "initial_status": "pending_approval",
            "recommended_action": "manager_review",
        },
    )


def test_create_manual_review_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual review should create a needs-review workflow."""

    document = Mock()
    document.id = 11

    business_rule_result = BusinessRuleResult(
        requires_approval=False,
        approval_role=None,
        requires_manual_review=True,
        next_action=BusinessAction.MANUAL_REVIEW,
        reason="Manual review is required.",
    )

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_by_document_id",
        Mock(return_value=None),
    )

    created_workflow = Mock()
    created_workflow.id = 21
    created_workflow.current_status = WorkflowStatus.NEEDS_REVIEW

    mock_create_workflow = Mock(return_value=created_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

    service.audit_log_service.record_event = Mock()

    workflow = service.create_from_business_rule(
        document=document,
        business_rule_result=business_rule_result,
    )

    assert workflow is created_workflow

    assert (
        mock_create_workflow.call_args.kwargs["current_status"]
        == WorkflowStatus.NEEDS_REVIEW
    )


def test_create_continue_processing_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Continue processing should create a completed workflow."""

    document = Mock()
    document.id = 12

    business_rule_result = BusinessRuleResult(
        requires_approval=False,
        approval_role=None,
        requires_manual_review=False,
        next_action=BusinessAction.CONTINUE_PROCESSING,
        reason="No additional review is required.",
    )

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_by_document_id",
        Mock(return_value=None),
    )

    created_workflow = Mock()
    created_workflow.id = 22
    created_workflow.current_status = WorkflowStatus.COMPLETED

    mock_create_workflow = Mock(return_value=created_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

    service.audit_log_service.record_event = Mock()

    service.create_from_business_rule(
        document=document,
        business_rule_result=business_rule_result,
    )

    assert (
        mock_create_workflow.call_args.kwargs["current_status"]
        == WorkflowStatus.COMPLETED
    )


def test_create_workflow_rejects_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A document should not receive a second workflow."""

    document = Mock()
    document.id = 13

    business_rule_result = BusinessRuleResult(
        requires_approval=True,
        approval_role=UserRole.MANAGER,
        requires_manual_review=False,
        next_action=BusinessAction.MANAGER_REVIEW,
        reason="Manager approval is required.",
    )

    existing_workflow = Mock()

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_by_document_id",
        Mock(return_value=existing_workflow),
    )

    mock_create_workflow = Mock()

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

    mock_record_event = Mock()
    service.audit_log_service.record_event = mock_record_event

    with pytest.raises(
        WorkflowAlreadyExistsError,
        match="A workflow already exists for this document",
    ):
        service.create_from_business_rule(
            document=document,
            business_rule_result=business_rule_result,
        )

    mock_create_workflow.assert_not_called()
    mock_record_event.assert_not_called()


def test_record_approved_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approved decisions should move the workflow to approved."""

    # Create a workflow waiting for manager approval.
    workflow = Mock()
    workflow.id = 5
    workflow.current_status = WorkflowStatus.PENDING_APPROVAL

    # Simulate retrieving the latest locked workflow.
    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_for_update",
        Mock(return_value=workflow),
    )

    # Simulate the approval record created in the database.
    created_approval = Mock()
    created_approval.id = 30

    mock_create_approval = Mock(
        return_value=created_approval,
    )

    # Simulate the workflow after approval.
    updated_workflow = Mock()
    updated_workflow.current_status = WorkflowStatus.APPROVED

    mock_update_status = Mock(
        return_value=updated_workflow,
    )

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        mock_create_approval,
    )

    monkeypatch.setattr(
        "app.services.workflow_service.update_workflow_status",
        mock_update_status,
    )

    # Create a mocked database session.
    mock_database_session = Mock()

    # Simulate an authorized admin submitting the decision.
    mock_approver = Mock(spec=User)
    mock_approver.id = 7
    mock_approver.role = UserRole.ADMIN

    # Return the authorized admin when the service looks up the user.
    mock_database_session.get.return_value = mock_approver

    service = WorkflowService(
        database_session=mock_database_session,
    )

    # Replace audit logging with a mock.
    mock_record_event = Mock()
    service.audit_log_service.record_event = mock_record_event

    # Execute the approval decision.
    result_workflow, approval = service.record_approval_decision(
        workflow=workflow,
        approver_id=7,
        decision=ApprovalDecision.APPROVED,
        comment="Approved for payment.",
    )

    # Verify the returned workflow and approval.
    assert result_workflow is updated_workflow
    assert approval is created_approval

    # Verify that the service retrieves the authorized admin.
    mock_database_session.get.assert_called_once_with(
        User,
        7,
    )

    # Verify that the approval is saved.
    mock_create_approval.assert_called_once_with(
        database_session=mock_database_session,
        workflow_id=5,
        approver_id=7,
        decision=ApprovalDecision.APPROVED,
        comment="Approved for payment.",
        commit=False,
    )

    # Verify that the workflow moves to APPROVED.
    mock_update_status.assert_called_once_with(
        database_session=mock_database_session,
        workflow=workflow,
        status=WorkflowStatus.APPROVED,
        commit=False,
    )

    # Verify that an audit event is recorded.
    mock_record_event.assert_called_once_with(
        user_id=7,
        action=AuditAction.WORKFLOW_APPROVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=5,
        event_metadata={
            "approval_id": 30,
            "previous_status": "pending_approval",
            "new_status": "approved",
        },
        commit=False,
    )

    # Verify that the transaction is committed.
    mock_database_session.commit.assert_called_once()


@pytest.mark.parametrize(
    ("decision", "expected_status", "expected_audit_action"),
    [
        (
            ApprovalDecision.REJECTED,
            WorkflowStatus.REJECTED,
            AuditAction.WORKFLOW_REJECTED,
        ),
        (
            ApprovalDecision.INFORMATION_REQUESTED,
            WorkflowStatus.NEEDS_INFORMATION,
            AuditAction.WORKFLOW_INFORMATION_REQUESTED,
        ),
    ],
)
def test_record_decision_updates_expected_status(
    monkeypatch: pytest.MonkeyPatch,
    decision: ApprovalDecision,
    expected_status: WorkflowStatus,
    expected_audit_action: AuditAction,
) -> None:
    """Approval decisions should map to workflow status and audit action."""

    workflow = Mock()
    workflow.id = 6
    workflow.current_status = WorkflowStatus.PENDING_APPROVAL

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_for_update",
        Mock(return_value=workflow),
    )

    created_approval = Mock()
    created_approval.id = 31

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        Mock(return_value=created_approval),
    )

    updated_workflow = Mock()
    updated_workflow.current_status = expected_status

    mock_update_status = Mock(return_value=updated_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.update_workflow_status",
        mock_update_status,
    )

    mock_create_information_request = Mock()
    monkeypatch.setattr(
        "app.services.workflow_service.create_information_request",
        mock_create_information_request,
    )

    mock_database_session = Mock()

    # Simulate an authorized admin for workflow decisions.
    mock_approver = Mock(spec=User)
    mock_approver.id = 8
    mock_approver.role = UserRole.ADMIN

    # Return the admin when WorkflowService looks up the user.
    mock_database_session.get.return_value = mock_approver

    service = WorkflowService(
        database_session=mock_database_session,
    )

    mock_record_event = Mock()
    service.audit_log_service.record_event = mock_record_event

    service.record_approval_decision(
        workflow=workflow,
        approver_id=8,
        decision=decision,
        comment=(
            "Please provide the missing information."
            if decision == ApprovalDecision.INFORMATION_REQUESTED
            else "The document contains incorrect information."
        ),
    )

    assert mock_update_status.call_args.kwargs["status"] == expected_status
    assert mock_update_status.call_args.kwargs["commit"] is False
    mock_database_session.commit.assert_called_once()

    if decision == ApprovalDecision.INFORMATION_REQUESTED:
        mock_create_information_request.assert_called_once_with(
            database_session=mock_database_session,
            workflow_id=6,
            requested_by=8,
            request_comment="Please provide the missing information.",
            return_status=WorkflowStatus.PENDING_APPROVAL.value,
            approval_id=31,
        )
    else:
        mock_create_information_request.assert_not_called()

    mock_record_event.assert_called_once_with(
        user_id=8,
        action=expected_audit_action,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=6,
        event_metadata={
            "approval_id": 31,
            "previous_status": "pending_approval",
            "new_status": expected_status.value,
        },
        commit=False,
    )


def test_record_decision_rejects_invalid_workflow_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only pending-approval workflows may receive approval decisions."""

    workflow = Mock()
    workflow.id = 7
    workflow.current_status = WorkflowStatus.COMPLETED

    monkeypatch.setattr(
        "app.services.workflow_service.get_workflow_for_update",
        Mock(return_value=workflow),
    )

    mock_create_approval = Mock()
    mock_update_status = Mock()

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        mock_create_approval,
    )

    monkeypatch.setattr(
        "app.services.workflow_service.update_workflow_status",
        mock_update_status,
    )

    mock_database_session = Mock()

    # Use an authorized admin so we can test the invalid status.
    mock_approver = Mock(spec=User)
    mock_approver.id = 7
    mock_approver.role = UserRole.ADMIN

    mock_database_session.get.return_value = mock_approver

    service = WorkflowService(
        database_session=mock_database_session,
    )

    mock_record_event = Mock()
    service.audit_log_service.record_event = mock_record_event

    with pytest.raises(
        InvalidWorkflowStateError,
        match="Workflow is not waiting for approval",
    ):
        service.record_approval_decision(
            workflow=workflow,
            approver_id=7,
            decision=ApprovalDecision.APPROVED,
        )

    mock_create_approval.assert_not_called()
    mock_update_status.assert_not_called()
    mock_record_event.assert_not_called()

    mock_database_session.rollback.assert_called_once()
