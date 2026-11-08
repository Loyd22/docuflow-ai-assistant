"""API integration tests for Admin Role Management."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import AuditAction, UserRole
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.services.audit_log_service import AuditLogService


def create_test_user(
    client: TestClient,
    db_session: Session,
    *,
    name: str,
    email: str,
    role: UserRole = UserRole.EMPLOYEE,
) -> User:
    """Register a test user and assign the requested role."""

    response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    user = db_session.scalar(select(User).where(User.email == email))

    assert user is not None

    user.role = role
    db_session.commit()

    return user


def login_as(
    client: TestClient,
    *,
    email: str,
) -> dict[str, str]:
    """Log in and return authentication headers."""

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200

    return {"Authorization": (f"Bearer {response.json()['access_token']}")}


def test_admin_can_change_employee_to_manager(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admin can change a user's role successfully."""

    create_test_user(
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

    headers = login_as(
        client,
        email="admin@example.com",
    )

    response = client.patch(
        f"/admin/users/{employee.id}/role",
        json={"role": "manager"},
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == employee.id
    assert data["role"] == "manager"

    # Confirm the database was updated.
    db_session.refresh(employee)
    assert employee.role == UserRole.MANAGER

    # Sensitive information must not be exposed.
    assert "password_hash" not in data
    assert "password" not in data


@pytest.mark.parametrize(
    "role",
    [
        UserRole.EMPLOYEE,
        UserRole.MANAGER,
    ],
)
def test_non_admin_cannot_change_user_roles(
    client: TestClient,
    db_session: Session,
    role: UserRole,
) -> None:
    """Employees and Managers cannot modify roles."""

    actor = create_test_user(
        client,
        db_session,
        name="Regular User",
        email="regular@example.com",
        role=role,
    )

    target = create_test_user(
        client,
        db_session,
        name="Target User",
        email="target@example.com",
    )

    headers = login_as(
        client,
        email=actor.email,
    )

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "admin"},
        headers=headers,
    )

    assert response.status_code == 403

    db_session.refresh(target)
    assert target.role == UserRole.EMPLOYEE


def test_admin_cannot_change_own_role(
    client: TestClient,
    db_session: Session,
) -> None:
    """Prevent an Admin from changing their own role."""

    admin = create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    headers = login_as(
        client,
        email=admin.email,
    )

    response = client.patch(
        f"/admin/users/{admin.id}/role",
        json={"role": "employee"},
        headers=headers,
    )

    assert response.status_code == 403

    db_session.refresh(admin)
    assert admin.role == UserRole.ADMIN


def test_admin_role_change_rejects_missing_user(
    client: TestClient,
    db_session: Session,
) -> None:
    """Return 404 when the target does not exist."""

    create_test_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    headers = login_as(
        client,
        email="admin@example.com",
    )

    response = client.patch(
        "/admin/users/999999/role",
        json={"role": "manager"},
        headers=headers,
    )

    assert response.status_code == 404


def test_admin_role_change_rejects_invalid_role(
    client: TestClient,
    db_session: Session,
) -> None:
    """Pydantic must reject unsupported roles."""

    create_test_user(
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

    headers = login_as(
        client,
        email="admin@example.com",
    )

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "superadmin"},
        headers=headers,
    )

    assert response.status_code == 422


def test_role_change_creates_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    """A successful role change must produce an audit event."""

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

    headers = login_as(
        client,
        email=admin.email,
    )

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "manager"},
        headers=headers,
    )

    assert response.status_code == 200

    statement = select(AuditLog).where(
        AuditLog.action == AuditAction.USER_ROLE_CHANGED,
        AuditLog.entity_id == target.id,
    )

    audit_log = db_session.scalar(statement)

    assert audit_log is not None
    assert audit_log.user_id == admin.id
    assert audit_log.event_metadata == {
        "previous_role": "employee",
        "new_role": "manager",
    }


def test_admin_can_demote_another_admin(
    client: TestClient,
    db_session: Session,
) -> None:
    """An Admin can demote another Admin when one remains."""

    actor = create_test_user(
        client,
        db_session,
        name="Admin Actor",
        email="actor@example.com",
        role=UserRole.ADMIN,
    )

    target = create_test_user(
        client,
        db_session,
        name="Admin Target",
        email="target@example.com",
        role=UserRole.ADMIN,
    )

    headers = login_as(client, email=actor.email)

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "manager"},
        headers=headers,
    )

    assert response.status_code == 200

    db_session.refresh(target)
    assert target.role == UserRole.MANAGER

    active_admins = db_session.scalars(
        select(User).where(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
        )
    ).all()

    assert len(active_admins) == 1
    assert active_admins[0].id == actor.id


def test_unchanged_role_does_not_create_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    """A role-change request with no change creates no audit event."""

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
        name="Manager User",
        email="manager@example.com",
        role=UserRole.MANAGER,
    )

    headers = login_as(client, email=admin.email)

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "manager"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "manager"

    audit_events = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == AuditAction.USER_ROLE_CHANGED,
            AuditLog.entity_id == target.id,
        )
    ).all()

    assert audit_events == []


def test_unauthenticated_request_cannot_change_roles(
    client: TestClient,
    db_session: Session,
) -> None:
    """A request without a valid token must be rejected."""

    target = create_test_user(
        client,
        db_session,
        name="Employee User",
        email="employee@example.com",
    )

    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "admin"},
    )

    assert response.status_code in (401, 403)

    db_session.refresh(target)
    assert target.role == UserRole.EMPLOYEE


def test_role_update_rolls_back_when_audit_fails(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed audit operation must roll back the role update."""

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
        name="Employee User",
        email="employee@example.com",
    )

    headers = login_as(client, email=admin.email)

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

    # By default, TestClient re-raises unhandled server exceptions.
    # Disable that behavior for this deliberately failing request.
    # Verify that the simulated audit failure propagates.
    with pytest.raises(
        RuntimeError,
        match="Simulated audit failure",
    ):
        client.patch(
            f"/admin/users/{target.id}/role",
            json={"role": "manager"},
            headers=headers,
        )

    # Re-read the user after the failed transaction.
    db_session.expire_all()

    stored_target = db_session.get(User, target.id)

    assert stored_target is not None
    assert stored_target.role == UserRole.EMPLOYEE
