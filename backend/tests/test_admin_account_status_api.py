"""API integration tests for Admin Account Status Management."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import AuditAction, UserRole
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.services.audit_log_service import AuditLogService
from tests.test_admin_role_management_api import (
    create_test_user,
    login_as,
)


def test_admin_can_deactivate_employee(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admin can deactivate an active employee."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    employee = create_test_user(
        client,
        db_session,
        name="Employee User",
        email="employee@example.com",
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{employee.id}/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    db_session.refresh(employee)
    assert employee.is_active is False
    assert "password_hash" not in response.json()


def test_admin_can_reactivate_employee(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admin can reactivate an inactive employee."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    employee = create_test_user(
        client,
        db_session,
        name="Employee User",
        email="employee@example.com",
    )

    employee.is_active = False
    db_session.commit()

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{employee.id}/status",
        json={"is_active": True},
        headers=headers,
    )

    assert response.status_code == 200

    db_session.refresh(employee)
    assert employee.is_active is True


@pytest.mark.parametrize(
    "role",
    [UserRole.EMPLOYEE, UserRole.MANAGER],
)
def test_non_admin_cannot_change_account_status(
    client: TestClient,
    db_session: Session,
    role: UserRole,
) -> None:
    """Only Admins can change another user's account status."""

    actor = create_test_user(
        client,
        db_session,
        name="Actor User",
        email="actor@example.com",
        role=role,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(client, email=actor.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 403

    db_session.refresh(target)
    assert target.is_active is True


def test_admin_cannot_deactivate_self(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admin self-deactivation is forbidden."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{admin.id}/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 403

    db_session.refresh(admin)
    assert admin.is_active is True


def test_account_status_rejects_missing_user(
    client: TestClient,
    db_session: Session,
) -> None:
    """Return 404 when the target account does not exist."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        "/admin/users/999999/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 404


def test_account_status_rejects_string_boolean(
    client: TestClient,
    db_session: Session,
) -> None:
    """StrictBool rejects strings instead of converting them."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": "false"},
        headers=headers,
    )

    assert response.status_code == 422


def test_unauthenticated_user_cannot_change_status(
    client: TestClient,
    db_session: Session,
) -> None:
    """Reject requests without a valid access token."""

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": False},
    )

    assert response.status_code in (401, 403)

    db_session.refresh(target)
    assert target.is_active is True


def test_unchanged_status_does_not_create_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    """An unchanged account status does not create an audit event."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": True},
        headers=headers,
    )

    assert response.status_code == 200

    audit_events = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == AuditAction.USER_STATUS_CHANGED,
            AuditLog.entity_id == target.id,
        )
    ).all()

    assert audit_events == []


def test_status_change_creates_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    """Account status changes must be audited."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200

    audit_log = db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == AuditAction.USER_STATUS_CHANGED,
            AuditLog.entity_id == target.id,
        )
    )

    assert audit_log is not None
    assert audit_log.user_id == admin.id
    assert audit_log.event_metadata == {
        "previous_is_active": True,
        "new_is_active": False,
    }


def test_deactivated_user_cannot_login(
    client: TestClient,
    db_session: Session,
) -> None:
    """An inactive account cannot obtain a new JWT."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": target.email,
            "password": "password123",
        },
    )

    assert login_response.status_code in (401, 403)


def test_deactivated_user_cannot_use_existing_jwt(
    client: TestClient,
    db_session: Session,
) -> None:
    """Previously issued JWTs cannot bypass deactivation."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    admin_headers = login_as(client, email=admin.email)

    # Obtain the employee token before deactivation.
    employee_headers = login_as(client, email=target.email)

    response = client.patch(
        f"/admin/users/{target.id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )

    assert response.status_code == 200

    # Reuse the JWT issued before account deactivation.
    protected_response = client.get(
        "/auth/me",
        headers=employee_headers,
    )

    assert protected_response.status_code == 403
    assert protected_response.json()["detail"] == ("User account is inactive.")


def test_status_change_rolls_back_when_audit_fails(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed audit operation must roll back the status change."""

    # Create an active administrator.
    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    # Create an active employee.
    target = create_test_user(
        client,
        db_session,
        name="Employee User",
        email="employee@example.com",
    )

    headers = login_as(client, email=admin.email)

    # Simulate an error during audit logging.
    def simulate_audit_failure(
        self: AuditLogService,
        **kwargs: object,
    ) -> None:
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        AuditLogService,
        "record_event",
        simulate_audit_failure,
    )

    # TestClient propagates unexpected server exceptions.
    with pytest.raises(
        RuntimeError,
        match="Simulated audit failure",
    ):
        client.patch(
            f"/admin/users/{target.id}/status",
            json={"is_active": False},
            headers=headers,
        )

    # Discard cached objects and reload the database state.
    db_session.expire_all()

    stored_target = db_session.get(User, target.id)

    assert stored_target is not None

    # The Employee must remain active after rollback.
    assert stored_target.is_active is True

    # No status-change audit event should have been committed.
    audit_events = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == AuditAction.USER_STATUS_CHANGED,
            AuditLog.entity_id == target.id,
        )
    ).all()

    assert audit_events == []
