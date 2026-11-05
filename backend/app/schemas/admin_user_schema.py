"""Response schemas for Admin User Management."""

from pydantic import BaseModel

from app.schemas.auth_schema import UserResponse


class UserListResponse(BaseModel):
    """Paginated list of users visible to administrators."""

    users: list[UserResponse]
    total: int
    limit: int
    offset: int
