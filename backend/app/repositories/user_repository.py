from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.enums import UserRole
from app.db.models.user import User

# Shared lock identifier for administrative membership changes.
ADMIN_MEMBERSHIP_LOCK_KEY = 15002001


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

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[User]:
        """Return a paginated list of users."""

        statement = select(User).order_by(User.id.asc()).limit(limit).offset(offset)

        return list(self.db_session.scalars(statement).all())

    def count_users(self) -> int:
        """Count all registered users."""

        statement = select(func.count()).select_from(User)

        return self.db_session.scalar(statement) or 0

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

    def lock_admin_membership(self) -> None:
        """Serialize changes that affect Admin membership."""

        self.db_session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": ADMIN_MEMBERSHIP_LOCK_KEY},
        )

    def get_by_id_for_update(self, user_id: int) -> User | None:
        """Lock a user record until the transaction ends."""

        statement = select(User).where(User.id == user_id).with_for_update()

        return self.db_session.scalar(statement)

    def count_active_admins(self) -> int:
        """Count currently active Admin accounts."""

        statement = (
            select(func.count())
            .select_from(User)
            .where(
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
            )
        )

        return self.db_session.scalar(statement) or 0
