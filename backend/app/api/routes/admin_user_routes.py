"""Admin-only endpoints for managing user accounts."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.admin_user_schema import UserListResponse
from app.services.admin_user_service import AdminUserService

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin User Management"],
)


@router.get(
    "",
    response_model=UserListResponse,
)
def list_users(
    db_session: Annotated[
        Session,
        Depends(get_db_session),
    ],
    current_admin: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN)),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserListResponse:
    """List registered users. Admin access only."""

    user_repository = UserRepository(db_session)
    admin_user_service = AdminUserService(user_repository)

    return admin_user_service.list_users(
        limit=limit,
        offset=offset,
    )
