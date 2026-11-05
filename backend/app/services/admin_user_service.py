"""Business operations for administrative user management."""

from app.repositories.user_repository import UserRepository
from app.schemas.admin_user_schema import UserListResponse


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

        # Get the requested page of users.
        users = self.user_repository.list_users(
            limit=limit,
            offset=offset,
        )

        # Count all users for pagination.
        total = self.user_repository.count_users()

        return UserListResponse(
            users=users,
            total=total,
            limit=limit,
            offset=offset,
        )
