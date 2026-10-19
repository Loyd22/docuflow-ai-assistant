"""
API integration tests for audit-log operations.

These tests verify that the FastAPI audit-log endpoint correctly:
- requires manager or admin authorization
- returns audit history for a specific entity
- returns audit records in chronological order
- returns an empty list when no audit history exists

The tests use the real PostgreSQL test database.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import (
    AuditAction,
    AuditEntityType,
    UserRole,
)
from app.db.models.audit_log import AuditLog
from app.db.models.user import User


def create_test_user_and_token(
    client: TestClient,
    db_session: Session,
    *,
    name: str,
    email: str,
    role: UserRole,
) -> tuple[User, str]:
    """Create a user, assign a role, and return an access token."""

    register_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user = db_session.query(User).filter(User.email == email).one()

    user.role = role
    db_session.commit()
    db_session.refresh(user)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    return user, access_token


def create_test_audit_log(
    db_session: Session,
    *,
    user_id: int | None,
    action: AuditAction,
    entity_type: AuditEntityType,
    entity_id: int,
    event_metadata: dict | None = None,
) -> AuditLog:
    """Create an audit-log record for API testing."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=event_metadata,
    )

    db_session.add(audit_log)
    db_session.commit()
    db_session.refresh(audit_log)

    return audit_log


def test_manager_can_view_entity_audit_history(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to retrieve audit history."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit Manager",
        email="audit-manager@example.com",
        role=UserRole.MANAGER,
    )

    audit_log = create_test_audit_log(
        db_session,
        user_id=manager.id,
        action=AuditAction.WORKFLOW_APPROVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=100,
        event_metadata={
            "previous_status": "pending_approval",
            "new_status": "approved",
        },
    )

    response = client.get(
        "/audit-logs/workflow/100",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 1

    returned_audit_log = response_data[0]

    assert returned_audit_log["id"] == audit_log.id
    assert returned_audit_log["user_id"] == manager.id
    assert returned_audit_log["action"] == "workflow_approved"
    assert returned_audit_log["entity_type"] == "workflow"
    assert returned_audit_log["entity_id"] == 100

    assert returned_audit_log["event_metadata"] == {
        "previous_status": "pending_approval",
        "new_status": "approved",
    }

    assert returned_audit_log["created_at"] is not None


def test_admin_can_view_entity_audit_history(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should be able to retrieve audit history."""

    admin, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit Admin",
        email="audit-admin@example.com",
        role=UserRole.ADMIN,
    )

    create_test_audit_log(
        db_session,
        user_id=admin.id,
        action=AuditAction.WORKFLOW_REJECTED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=101,
        event_metadata={
            "previous_status": "pending_approval",
            "new_status": "rejected",
        },
    )

    response = client.get(
        "/audit-logs/workflow/101",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 1
    assert response_data[0]["action"] == "workflow_rejected"
    assert response_data[0]["entity_type"] == "workflow"
    assert response_data[0]["entity_id"] == 101


def test_employee_cannot_view_entity_audit_history(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should not be allowed to retrieve audit history."""

    employee, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit Employee",
        email="audit-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    create_test_audit_log(
        db_session,
        user_id=employee.id,
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type=AuditEntityType.DOCUMENT,
        entity_id=102,
    )

    response = client.get(
        "/audit-logs/document/102",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403


def test_audit_history_is_returned_in_chronological_order(
    client: TestClient,
    db_session: Session,
) -> None:
    """Audit history should be returned from oldest to newest."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Timeline Manager",
        email="timeline-manager@example.com",
        role=UserRole.MANAGER,
    )

    first_audit_log = create_test_audit_log(
        db_session,
        user_id=None,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=103,
        event_metadata={
            "initial_status": "pending_approval",
        },
    )

    second_audit_log = create_test_audit_log(
        db_session,
        user_id=manager.id,
        action=AuditAction.WORKFLOW_APPROVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=103,
        event_metadata={
            "previous_status": "pending_approval",
            "new_status": "approved",
        },
    )

    response = client.get(
        "/audit-logs/workflow/103",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 2

    assert response_data[0]["id"] == first_audit_log.id
    assert response_data[0]["action"] == "workflow_created"

    assert response_data[1]["id"] == second_audit_log.id
    assert response_data[1]["action"] == "workflow_approved"


def test_entity_without_audit_history_returns_empty_list(
    client: TestClient,
    db_session: Session,
) -> None:
    """Entities without audit events should return an empty history."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Empty Audit Manager",
        email="empty-audit-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        "/audit-logs/workflow/999999",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_manager_can_list_all_audit_logs(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to retrieve the full audit log."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit List Manager",
        email="audit-list-manager@example.com",
        role=UserRole.MANAGER,
    )

    audit_log = create_test_audit_log(
        db_session,
        user_id=manager.id,
        action=AuditAction.WORKFLOW_APPROVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=200,
        event_metadata={
            "new_status": "approved",
        },
    )

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    audit_log_ids = {
        item["id"]
        for item in response_data
    }

    assert audit_log.id in audit_log_ids


def test_admin_can_list_all_audit_logs(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should be able to retrieve the full audit log."""

    admin, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit List Admin",
        email="audit-list-admin@example.com",
        role=UserRole.ADMIN,
    )

    audit_log = create_test_audit_log(
        db_session,
        user_id=admin.id,
        action=AuditAction.WORKFLOW_REJECTED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=201,
        event_metadata={
            "new_status": "rejected",
        },
    )

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    audit_log_ids = {
        item["id"]
        for item in response.json()
    }

    assert audit_log.id in audit_log_ids


def test_employee_cannot_list_all_audit_logs(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should not be allowed to view the full audit log."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit List Employee",
        email="audit-list-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403


def test_list_audit_logs_requires_authentication(
    client: TestClient,
) -> None:
    """The full audit log should require authentication."""

    response = client.get("/audit-logs")

    assert response.status_code == 401


def test_all_audit_logs_are_returned_newest_first(
    client: TestClient,
    db_session: Session,
) -> None:
    """The main audit-log endpoint should return newest events first."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Audit Order Manager",
        email="audit-order-manager@example.com",
        role=UserRole.MANAGER,
    )

    first_audit_log = create_test_audit_log(
        db_session,
        user_id=manager.id,
        action=AuditAction.WORKFLOW_CREATED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=202,
    )

    second_audit_log = create_test_audit_log(
        db_session,
        user_id=manager.id,
        action=AuditAction.WORKFLOW_APPROVED,
        entity_type=AuditEntityType.WORKFLOW,
        entity_id=202,
    )

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    returned_ids = [
        item["id"]
        for item in response_data
    ]

    first_index = returned_ids.index(
        first_audit_log.id,
    )
    second_index = returned_ids.index(
        second_audit_log.id,
    )

    # The second event was created later,
    # so it should appear earlier in the list.
    assert second_index < first_index