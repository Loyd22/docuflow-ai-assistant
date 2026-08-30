from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import UserRole
from app.db.models.user import User


class UserRepository:
    """Database operations related to users."""

    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by primary key."""

        statement = select(User).where(User.id == user_id)

        return self.db_session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email address."""

        statement = select(User).where(User.email == email)

        return self.db_session.scalar(statement)

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        """Create and persist a new user."""

        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
        )

        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)

        return user
