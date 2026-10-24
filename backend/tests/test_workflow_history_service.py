"""Tests for workflow history ordering."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.db.enums import AuditEntityType
from app.services.workflow_history_service import WorkflowHistoryService


def test_history_follows_audit_event_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual reviews appear before approvals when audit events say so."""

    # Give both decisions exactly the same timestamp.
    timestamp = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)

    review = SimpleNamespace(
        id=10,
        reviewer_id=2,
        outcome=SimpleNamespace(value="resolved"),
        comment="Invoice verified.",
        created_at=timestamp,
    )

    approval = SimpleNamespace(
        id=20,
        approver_id=2,
        decision=SimpleNamespace(value="approved"),
        comment="Approved for payment.",
        created_at=timestamp,
    )

    # Provide audit events in the opposite input order.
    approval_event = SimpleNamespace(
        id=102,
        event_metadata={"approval_id": 20},
    )

    review_event = SimpleNamespace(
        id=101,
        event_metadata={"review_id": 10},
    )

    # Replace repository queries with controlled test records.
    monkeypatch.setattr(
        "app.services.workflow_history_service.get_approvals_by_workflow_id",
        Mock(return_value=[approval]),
    )

    monkeypatch.setattr(
        "app.services.workflow_history_service.get_reviews_by_workflow_id",
        Mock(return_value=[review]),
    )

    # This workflow has no employee information requests.
    monkeypatch.setattr(
        "app.services.workflow_history_service.get_information_requests_by_workflow_id",
        Mock(return_value=[]),
    )

    mock_get_audit_logs = Mock(
        return_value=[approval_event, review_event],
    )

    monkeypatch.setattr(
        "app.services.workflow_history_service.get_audit_logs_by_entity",
        mock_get_audit_logs,
    )

    service = WorkflowHistoryService(
        database_session=Mock(),
    )

    result = service.get_history(workflow_id=5)

    # Verify audit-event IDs determine the final ordering.
    assert result.workflow_id == 5
    assert len(result.history) == 2

    assert result.history[0].action_type == "manual_review"
    assert result.history[0].decision == "resolved"

    assert result.history[1].action_type == "approval"
    assert result.history[1].decision == "approved"

    # Confirm the correct workflow audit events were retrieved.
    mock_get_audit_logs.assert_called_once_with(
        database_session=service.database_session,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=5,
    )


def test_history_preserves_decisions_without_audit_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Older decisions remain visible without matching audit logs."""

    timestamp = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)

    # Simulate an approval without an audit record.
    approval = SimpleNamespace(
        id=20,
        approver_id=2,
        decision=SimpleNamespace(value="approved"),
        comment="Approved previously.",
        created_at=timestamp,
    )

    # Simulate a manual review without an audit record.
    review = SimpleNamespace(
        id=10,
        reviewer_id=3,
        outcome=SimpleNamespace(value="resolved"),
        comment="Previously verified.",
        created_at=timestamp,
    )

    # Return existing decisions from the repositories.
    monkeypatch.setattr(
        "app.services.workflow_history_service.get_approvals_by_workflow_id",
        Mock(return_value=[approval]),
    )

    monkeypatch.setattr(
        "app.services.workflow_history_service.get_reviews_by_workflow_id",
        Mock(return_value=[review]),
    )

    # Simulate a workflow without employee information requests.
    monkeypatch.setattr(
        "app.services.workflow_history_service.get_information_requests_by_workflow_id",
        Mock(return_value=[]),
    )

    # Simulate older records without corresponding audit events.
    monkeypatch.setattr(
        "app.services.workflow_history_service.get_audit_logs_by_entity",
        Mock(return_value=[]),
    )

    service = WorkflowHistoryService(
        database_session=Mock(),
    )

    result = service.get_history(workflow_id=5)

    # Neither decision should be lost.
    assert result.workflow_id == 5
    assert len(result.history) == 2

    history_by_type = {item.action_type: item for item in result.history}

    assert set(history_by_type) == {
        "approval",
        "manual_review",
    }

    assert history_by_type["approval"].decision == "approved"
    assert history_by_type["manual_review"].decision == "resolved"

    # Confirm timestamps are retained.
    assert all(item.created_at == timestamp for item in result.history)
