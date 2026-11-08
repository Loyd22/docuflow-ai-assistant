"""Concurrency tests for administrative role changes."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.enums import AuditAction, AuditEntityType, UserRole
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.admin_user_service import (
    AdminUserService,
    RoleChangeForbiddenError,
)
from tests.conftest import TestSessionLocal


def test_concurrent_admin_demotions_leave_one_active_admin() -> None:
    """Two simultaneous demotions cannot remove every Admin."""

    # Give test accounts unique emails.
    unique_id = uuid4().hex

    admin_a = User(
        name="Concurrency Admin A",
        email=f"admin-a-{unique_id}@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )

    admin_b = User(
        name="Concurrency Admin B",
        email=f"admin-b-{unique_id}@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN,
        is_active=True,
    )

    # Commit setup data so independent connections can see it.
    with TestSessionLocal() as session:
        session.add_all([admin_a, admin_b])
        session.flush()

        admin_a_id = admin_a.id
        admin_b_id = admin_b.id

        session.commit()

    user_ids = [admin_a_id, admin_b_id]

    # Coordinate when both threads begin their requests.
    barrier = Barrier(2)

    def attempt_demote(
        actor_id: int,
        target_id: int,
    ) -> str:
        # Each thread gets its own database session.
        with TestSessionLocal() as session:
            service = AdminUserService(UserRepository(session))

            barrier.wait(timeout=10)

            try:
                service.change_role(
                    actor_id=actor_id,
                    target_user_id=target_id,
                    new_role=UserRole.EMPLOYEE,
                )
                return "success"

            except RoleChangeForbiddenError:
                return "forbidden"

    try:
        # Both operations are submitted concurrently.
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(
                attempt_demote,
                admin_a_id,
                admin_b_id,
            )

            future_b = executor.submit(
                attempt_demote,
                admin_b_id,
                admin_a_id,
            )

            results = [
                future_a.result(timeout=20),
                future_b.result(timeout=20),
            ]

        # Exactly one request should succeed.
        assert sorted(results) == ["forbidden", "success"]

        with TestSessionLocal() as session:
            users = session.scalars(select(User).where(User.id.in_(user_ids))).all()

            active_admins = [
                user for user in users if user.role == UserRole.ADMIN and user.is_active
            ]

            assert len(active_admins) == 1

            # Only one successful change should be audited.
            audit_events = session.scalars(
                select(AuditLog).where(
                    AuditLog.action == AuditAction.USER_ROLE_CHANGED,
                    AuditLog.entity_type == AuditEntityType.USER,
                    AuditLog.entity_id.in_(user_ids),
                )
            ).all()

            assert len(audit_events) == 1

    finally:
        # Clean up committed test data.
        with TestSessionLocal() as session:
            session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == AuditEntityType.USER,
                    AuditLog.entity_id.in_(user_ids),
                )
            )

            session.execute(delete(User).where(User.id.in_(user_ids)))

            session.commit()
