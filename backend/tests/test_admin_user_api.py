"""API tests for administrative user listing."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import UserRole
from app.db.models.user import User


def create_authenticated_user(
    client: TestClient,
    db_session: Session,
    *,
    name: str,
    email: str,
    role: UserRole,
) -> dict[str, str]:
    """Create a test user and return authorization headers."""

    register_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    # Set the role directly in the isolated test database.
    user = db_session.query(User).filter(User.email == email).one()

    user.role = role
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_admin_can_list_users(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins can retrieve registered user accounts."""

    headers = create_authenticated_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.get(
        "/admin/users",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["users"]) == 1

    user = data["users"][0]

    assert user["email"] == "admin@example.com"
    assert user["role"] == "admin"
    assert user["is_active"] is True

    # Sensitive credentials must never appear in the response.
    assert "password" not in user
    assert "password_hash" not in user


@pytest.mark.parametrize(
    "role",
    [
        UserRole.EMPLOYEE,
        UserRole.MANAGER,
    ],
)
def test_non_admin_cannot_list_users(
    client: TestClient,
    db_session: Session,
    role: UserRole,
) -> None:
    """Employees and managers cannot access the user directory."""

    headers = create_authenticated_user(
        client,
        db_session,
        name="Regular User",
        email="regular@example.com",
        role=role,
    )

    response = client.get(
        "/admin/users",
        headers=headers,
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_users(
    client: TestClient,
) -> None:
    """Requests without authentication are rejected."""

    response = client.get("/admin/users")

    assert response.status_code in (401, 403)


def test_admin_user_listing_pagination(
    client: TestClient,
    db_session: Session,
) -> None:
    """Pagination returns the requested users and total count."""

    headers = create_authenticated_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    for index in range(3):
        response = client.post(
            "/auth/register",
            json={
                "name": f"Employee {index}",
                "email": f"employee{index}@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 201

    first_page = client.get(
        "/admin/users",
        params={"limit": 2, "offset": 0},
        headers=headers,
    )

    second_page = client.get(
        "/admin/users",
        params={"limit": 2, "offset": 2},
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_data = first_page.json()
    second_data = second_page.json()

    assert first_data["total"] == 4
    assert second_data["total"] == 4

    assert len(first_data["users"]) == 2
    assert len(second_data["users"]) == 2

    first_ids = [user["id"] for user in first_data["users"]]
    second_ids = [user["id"] for user in second_data["users"]]

    # Pages should contain different users.
    assert set(first_ids).isdisjoint(second_ids)

    # User IDs should follow the expected stable ordering.
    assert first_ids == sorted(first_ids)
    assert second_ids == sorted(second_ids)
    assert max(first_ids) < min(second_ids)


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"limit": "invalid"},
    ],
)
def test_admin_listing_rejects_invalid_pagination(
    client: TestClient,
    db_session: Session,
    params: dict[str, int | str],
) -> None:
    """Invalid pagination inputs are rejected."""

    headers = create_authenticated_user(
        client,
        db_session,
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.get(
        "/admin/users",
        params=params,
        headers=headers,
    )

    assert response.status_code == 422
