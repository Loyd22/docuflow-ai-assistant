"""
Unit tests for the workflow and approval service.

These tests verify that WorkflowService correctly:
- converts Phase 8 business-rule decisions into workflow states
- prevents duplicate workflows
- records approval decisions
- updates workflow status after approval decisions
- rejects decisions for workflows that are not pending approval

Repository operations are mocked so these tests remain fast
and deterministic.
"""

from unittest.mock import Mock

import pytest

from app.db.enums import (
    ApprovalDecision,
    UserRole,
    WorkflowStatus,
)
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

    mock_create_workflow = Mock(return_value=created_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

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

    mock_create_workflow = Mock(return_value=created_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.create_workflow",
        mock_create_workflow,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

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

    with pytest.raises(
        WorkflowAlreadyExistsError,
        match="A workflow already exists for this document",
    ):
        service.create_from_business_rule(
            document=document,
            business_rule_result=business_rule_result,
        )

    mock_create_workflow.assert_not_called()


def test_record_approved_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approved decisions should move the workflow to approved."""

    workflow = Mock()
    workflow.id = 5
    workflow.current_status = WorkflowStatus.PENDING_APPROVAL

    created_approval = Mock()

    mock_create_approval = Mock(return_value=created_approval)

    updated_workflow = Mock()
    updated_workflow.current_status = WorkflowStatus.APPROVED

    mock_update_status = Mock(return_value=updated_workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        mock_create_approval,
    )

    monkeypatch.setattr(
        "app.services.workflow_service.update_workflow_status",
        mock_update_status,
    )

    mock_database_session = Mock()

    service = WorkflowService(
        database_session=mock_database_session,
    )

    result_workflow, approval = service.record_approval_decision(
        workflow=workflow,
        approver_id=7,
        decision=ApprovalDecision.APPROVED,
        comment="Approved for payment.",
    )

    assert result_workflow is updated_workflow
    assert approval is created_approval

    mock_create_approval.assert_called_once_with(
        database_session=mock_database_session,
        workflow_id=5,
        approver_id=7,
        decision=ApprovalDecision.APPROVED,
        comment="Approved for payment.",
    )

    mock_update_status.assert_called_once_with(
        database_session=mock_database_session,
        workflow=workflow,
        status=WorkflowStatus.APPROVED,
    )


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        (
            ApprovalDecision.REJECTED,
            WorkflowStatus.REJECTED,
        ),
        (
            ApprovalDecision.INFORMATION_REQUESTED,
            WorkflowStatus.NEEDS_INFORMATION,
        ),
    ],
)
def test_record_decision_updates_expected_status(
    monkeypatch: pytest.MonkeyPatch,
    decision: ApprovalDecision,
    expected_status: WorkflowStatus,
) -> None:
    """Approval decisions should map to the expected workflow status."""

    workflow = Mock()
    workflow.id = 6
    workflow.current_status = WorkflowStatus.PENDING_APPROVAL

    monkeypatch.setattr(
        "app.services.workflow_service.create_approval",
        Mock(return_value=Mock()),
    )

    mock_update_status = Mock(return_value=workflow)

    monkeypatch.setattr(
        "app.services.workflow_service.update_workflow_status",
        mock_update_status,
    )

    service = WorkflowService(
        database_session=Mock(),
    )

    service.record_approval_decision(
        workflow=workflow,
        approver_id=8,
        decision=decision,
    )

    assert mock_update_status.call_args.kwargs["status"] == expected_status


def test_record_decision_rejects_invalid_workflow_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only pending-approval workflows may receive approval decisions."""

    workflow = Mock()
    workflow.id = 7
    workflow.current_status = WorkflowStatus.COMPLETED

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

    service = WorkflowService(
        database_session=Mock(),
    )

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
