"""Schemas for administrative user management."""

from pydantic import BaseModel

from app.db.enums import UserRole
from app.schemas.auth_schema import UserResponse


class UserListResponse(BaseModel):
    """Paginated list of users visible to administrators."""

    users: list[UserResponse]
    total: int
    limit: int
    offset: int


class UserRoleUpdateRequest(BaseModel):
    """Data required to change an existing user's role."""

    role: UserRole
