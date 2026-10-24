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


def _build_history_with_records(
    monkeypatch: pytest.MonkeyPatch,
    *,
    approvals=None,
    reviews=None,
    information_requests=None,
    audit_logs=None,
):
    """Build history using controlled test records."""

    repository_results = {
        "get_approvals_by_workflow_id": approvals or [],
        "get_reviews_by_workflow_id": reviews or [],
        "get_information_requests_by_workflow_id": (information_requests or []),
        "get_audit_logs_by_entity": audit_logs or [],
    }

    # Replace database queries with our test records.
    for repository_name, records in repository_results.items():
        monkeypatch.setattr(
            f"app.services.workflow_history_service.{repository_name}",
            Mock(return_value=records),
        )

    service = WorkflowHistoryService(database_session=Mock())
    return service.get_history(workflow_id=5)


def test_history_skips_unanswered_information_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unanswered request must not appear as a response."""

    request = SimpleNamespace(
        id=30,
        responded_at=None,
        responded_by=None,
        response_comment=None,
        approval_id=20,
        review_id=None,
    )

    result = _build_history_with_records(
        monkeypatch,
        information_requests=[request],
    )

    assert result.workflow_id == 5
    assert result.history == []


@pytest.mark.parametrize(
    ("parent_type", "parent_field"),
    [
        ("approval", "approval_id"),
        ("manual_review", "review_id"),
    ],
)
def test_history_places_response_after_parent_decision(
    monkeypatch: pytest.MonkeyPatch,
    parent_type: str,
    parent_field: str,
) -> None:
    """Employee responses follow their related manager decisions."""

    decision_time = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    response_time = datetime(2026, 10, 22, 11, 0, tzinfo=timezone.utc)

    approval = SimpleNamespace(
        id=20,
        approver_id=2,
        decision=SimpleNamespace(value="information_requested"),
        comment="Please clarify this invoice.",
        created_at=decision_time,
    )

    review = SimpleNamespace(
        id=20,
        reviewer_id=2,
        outcome=SimpleNamespace(value="information_requested"),
        comment="Please clarify this invoice.",
        created_at=decision_time,
    )

    request = SimpleNamespace(
        id=30,
        responded_at=response_time,
        responded_by=3,
        response_comment="Here are the requested details.",
        approval_id=20 if parent_field == "approval_id" else None,
        review_id=20 if parent_field == "review_id" else None,
    )

    result = _build_history_with_records(
        monkeypatch,
        approvals=[approval] if parent_type == "approval" else [],
        reviews=[review] if parent_type == "manual_review" else [],
        information_requests=[request],
    )

    assert len(result.history) == 2
    assert [item.action_type for item in result.history] == [
        parent_type,
        "information_response",
    ]

    response = result.history[1]

    assert response.id == 30
    assert response.decided_by == 3
    assert response.decision == "responded"
    assert response.comment == "Here are the requested details."
    assert response.created_at == response_time


def test_history_orders_unlinked_response_by_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unlinked response uses its own timestamp for ordering."""

    early_time = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)
    response_time = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    late_time = datetime(2026, 10, 22, 11, 0, tzinfo=timezone.utc)

    early_approval = SimpleNamespace(
        id=10,
        approver_id=2,
        decision=SimpleNamespace(value="approved"),
        comment="Earlier approval.",
        created_at=early_time,
    )

    late_approval = SimpleNamespace(
        id=20,
        approver_id=2,
        decision=SimpleNamespace(value="approved"),
        comment="Later approval.",
        created_at=late_time,
    )

    request = SimpleNamespace(
        id=30,
        responded_at=response_time,
        responded_by=3,
        response_comment="An older unlinked response.",
        approval_id=None,
        review_id=None,
    )

    result = _build_history_with_records(
        monkeypatch,
        approvals=[late_approval, early_approval],
        information_requests=[request],
    )

    assert [item.id for item in result.history] == [10, 30, 20]
    assert [item.action_type for item in result.history] == [
        "approval",
        "information_response",
        "approval",
    ]


def test_history_orders_multiple_responses_to_same_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replies to one manager decision stay in response-time order."""

    decision_time = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)
    first_time = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 10, 22, 11, 0, tzinfo=timezone.utc)

    approval = SimpleNamespace(
        id=20,
        approver_id=2,
        decision=SimpleNamespace(value="information_requested"),
        comment="Additional details needed.",
        created_at=decision_time,
    )

    first_response = SimpleNamespace(
        id=31,
        responded_at=first_time,
        responded_by=3,
        response_comment="First response.",
        approval_id=20,
        review_id=None,
    )

    second_response = SimpleNamespace(
        id=32,
        responded_at=second_time,
        responded_by=3,
        response_comment="Second response.",
        approval_id=20,
        review_id=None,
    )

    # Intentionally provide responses in reverse order.
    result = _build_history_with_records(
        monkeypatch,
        approvals=[approval],
        information_requests=[second_response, first_response],
    )

    assert [item.id for item in result.history] == [20, 31, 32]
    assert [item.action_type for item in result.history] == [
        "approval",
        "information_response",
        "information_response",
    ]
