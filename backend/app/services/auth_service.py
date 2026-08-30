from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, RegisterRequest


class EmailAlreadyExistsError(Exception):
    """Raised when registration uses an email that already exists."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are incorrect."""


class InactiveUserError(Exception):
    """Raised when an inactive account attempts to authenticate."""


class AuthService:
    """Business logic for authentication operations."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register(self, request: RegisterRequest) -> User:
        """Register a new user account."""

        normalized_email = self._normalize_email(request.email)

        existing_user = self.user_repository.get_by_email(normalized_email)

        if existing_user is not None:
            raise EmailAlreadyExistsError("A user with this email already exists.")

        password_hash = hash_password(request.password)

        return self.user_repository.create(
            name=request.name.strip(),
            email=normalized_email,
            password_hash=password_hash,
        )

    def login(self, request: LoginRequest) -> str:
        """Authenticate a user and return an access token."""

        normalized_email = self._normalize_email(request.email)

        user = self.user_repository.get_by_email(normalized_email)

        if user is None:
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InactiveUserError("User account is inactive.")

        password_is_valid = verify_password(
            request.password,
            user.password_hash,
        )

        if not password_is_valid:
            raise InvalidCredentialsError("Invalid email or password.")

        return create_access_token(subject=str(user.id))

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Normalize email before database lookup or persistence."""

        return email.strip().lower()
