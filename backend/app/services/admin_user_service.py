"""Business operations for administrative user management."""

from sqlalchemy.orm import Session

from app.db.enums import AuditAction, AuditEntityType, UserRole
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.admin_user_schema import UserListResponse
from app.services.audit_log_service import AuditLogService


class UserNotFoundError(Exception):
    """Raised when the target user does not exist."""


class RoleChangeForbiddenError(Exception):
    """Raised when an actor cannot perform a role change."""


class LastActiveAdminError(Exception):
    """Raised when a change would remove the final active Admin."""


class AdminUserService:
    """Coordinate user-management operations."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
    ) -> UserListResponse:
        """Return a paginated list of registered users."""

        users = self.user_repository.list_users(
            limit=limit,
            offset=offset,
        )

        total = self.user_repository.count_users()

        return UserListResponse(
            users=users,
            total=total,
            limit=limit,
            offset=offset,
        )

    def change_role(
        self,
        *,
        actor_id: int,
        target_user_id: int,
        new_role: UserRole,
    ) -> User:
        """Change a user role and record the event atomically."""

        db_session: Session = self.user_repository.db_session

        try:
            # Serialize administrative membership changes.
            self.user_repository.lock_admin_membership()

            # Lock the acting Admin's current database record.
            actor = self.user_repository.get_by_id_for_update(actor_id)

            if actor is None or not actor.is_active or actor.role != UserRole.ADMIN:
                raise RoleChangeForbiddenError(
                    "Only active administrators may change user roles."
                )

            # Prevent an Admin from changing their own role.
            if actor_id == target_user_id:
                raise RoleChangeForbiddenError(
                    "Administrators cannot change their own role."
                )

            # Lock the target account before evaluating its state.
            target_user = self.user_repository.get_by_id_for_update(target_user_id)

            if target_user is None:
                raise UserNotFoundError("User account was not found.")

            previous_role = target_user.role

            # No database update or audit event for an unchanged role.
            if previous_role == new_role:
                db_session.commit()
                return target_user

            # Ensure at least one active administrator remains.
            if previous_role == UserRole.ADMIN and target_user.is_active:
                active_admin_count = self.user_repository.count_active_admins()

                if active_admin_count <= 1:
                    raise LastActiveAdminError(
                        "Cannot remove the last active administrator."
                    )

            # Stage the role update without committing yet.
            target_user.role = new_role

            audit_log_service = AuditLogService(db_session)

            audit_log_service.record_event(
                user_id=actor.id,
                action=AuditAction.USER_ROLE_CHANGED,
                entity_type=AuditEntityType.USER,
                entity_id=target_user.id,
                event_metadata={
                    "previous_role": previous_role.value,
                    "new_role": new_role.value,
                },
                commit=False,
            )

            # Execute pending changes before committing.
            db_session.flush()

            # Reload the updated record within the transaction.
            db_session.refresh(target_user)

            # Commit the role update and audit event together.
            db_session.commit()

            return target_user

        except Exception:
            db_session.rollback()
            raise
