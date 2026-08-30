import pytest

from app.core.security import hash_password, verify_password
from app.db.enums import UserRole
from app.db.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
)


class FakeUserRepository:
    """Small in-memory repository used only for AuthService unit tests."""

    def __init__(self) -> None:
        self.users: list[User] = []
        self.next_id = 1

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by ID."""

        for user in self.users:
            if user.id == user_id:
                return user

        return None

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email."""

        for user in self.users:
            if user.email == email:
                return user

        return None

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        """Create a user in memory."""

        user = User(
            id=self.next_id,
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )

        self.next_id += 1
        self.users.append(user)

        return user


def test_register_creates_user() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    request = RegisterRequest(
        name="Test Employee",
        email="TEST@example.com",
        password="password123",
    )

    user = auth_service.register(request)

    assert user.id == 1
    assert user.name == "Test Employee"
    assert user.email == "test@example.com"
    assert user.role == UserRole.EMPLOYEE
    assert user.is_active is True

    assert user.password_hash != "password123"

    assert verify_password(
        "password123",
        user.password_hash,
    )


def test_register_rejects_duplicate_email() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    first_request = RegisterRequest(
        name="First User",
        email="test@example.com",
        password="password123",
    )

    auth_service.register(first_request)

    duplicate_request = RegisterRequest(
        name="Second User",
        email="TEST@example.com",
        password="different123",
    )

    with pytest.raises(EmailAlreadyExistsError):
        auth_service.register(duplicate_request)


def test_login_returns_access_token() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    registration = RegisterRequest(
        name="Test Employee",
        email="test@example.com",
        password="password123",
    )

    auth_service.register(registration)

    login_request = LoginRequest(
        email="test@example.com",
        password="password123",
    )

    access_token = auth_service.login(login_request)

    assert isinstance(access_token, str)
    assert access_token


def test_login_rejects_wrong_password() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    registration = RegisterRequest(
        name="Test Employee",
        email="test@example.com",
        password="password123",
    )

    auth_service.register(registration)

    login_request = LoginRequest(
        email="test@example.com",
        password="wrongpassword",
    )

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(login_request)


def test_login_rejects_unknown_email() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    login_request = LoginRequest(
        email="missing@example.com",
        password="password123",
    )

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(login_request)


def test_login_rejects_inactive_user() -> None:
    repository = FakeUserRepository()
    auth_service = AuthService(repository)

    user = User(
        id=1,
        name="Inactive User",
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.EMPLOYEE,
        is_active=False,
    )

    repository.users.append(user)

    login_request = LoginRequest(
        email="inactive@example.com",
        password="password123",
    )

    with pytest.raises(InactiveUserError):
        auth_service.login(login_request)
