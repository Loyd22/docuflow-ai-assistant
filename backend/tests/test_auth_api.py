from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import UserRole
from app.db.models.user import User


def test_register_user(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Employee",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == "Test Employee"
    assert response_data["email"] == "test@example.com"
    assert response_data["role"] == "employee"
    assert response_data["is_active"] is True

    # Sensitive password information must never leave the API.
    assert "password" not in response_data
    assert "password_hash" not in response_data


def test_register_rejects_duplicate_email(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/auth/register",
        json={
            "name": "First User",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json={
            "name": "Second User",
            "email": "TEST@example.com",
            "password": "different123",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A user with this email already exists."
    )


def test_login_returns_access_token(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Test Employee",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    response_data = login_response.json()

    assert isinstance(response_data["access_token"], str)
    assert response_data["access_token"]
    assert response_data["token_type"] == "bearer"


def test_login_rejects_wrong_password(
    client: TestClient,
) -> None:
    client.post(
        "/auth/register",
        json={
            "name": "Test Employee",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_rejects_unknown_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "missing@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_get_current_user_with_valid_token(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Test Employee",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["name"] == "Test Employee"
    assert response_data["email"] == "test@example.com"
    assert response_data["role"] == "employee"
    assert response_data["is_active"] is True

    # Sensitive fields must not be returned.
    assert "password" not in response_data
    assert "password_hash" not in response_data


def test_get_current_user_without_token(
    client: TestClient,
) -> None:
    response = client.get("/auth/me")

    assert response.status_code in (401, 403)


def test_get_current_user_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer this-is-not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == ("Could not validate credentials.")


def test_employee_cannot_access_manager_or_admin_routes(
    client: TestClient,
) -> None:
    client.post(
        "/auth/register",
        json={
            "name": "Employee User",
            "email": "employee@example.com",
            "password": "password123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "employee@example.com",
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    manager_response = client.get(
        "/auth/manager-test",
        headers=headers,
    )

    admin_response = client.get(
        "/auth/admin-test",
        headers=headers,
    )

    assert manager_response.status_code == 403
    assert admin_response.status_code == 403


def test_manager_can_access_manager_route_but_not_admin_route(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/auth/register",
        json={
            "name": "Manager User",
            "email": "manager@example.com",
            "password": "password123",
        },
    )

    user = db_session.query(User).filter(User.email == "manager@example.com").one()

    user.role = UserRole.MANAGER
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager@example.com",
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    manager_response = client.get(
        "/auth/manager-test",
        headers=headers,
    )

    admin_response = client.get(
        "/auth/admin-test",
        headers=headers,
    )

    assert manager_response.status_code == 200
    assert admin_response.status_code == 403


def test_admin_can_access_manager_and_admin_routes(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/auth/register",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "password123",
        },
    )

    user = db_session.query(User).filter(User.email == "admin@example.com").one()

    user.role = UserRole.ADMIN
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    manager_response = client.get(
        "/auth/manager-test",
        headers=headers,
    )

    admin_response = client.get(
        "/auth/admin-test",
        headers=headers,
    )

    assert manager_response.status_code == 200
    assert admin_response.status_code == 200
