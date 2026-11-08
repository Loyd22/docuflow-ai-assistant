from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.admin_user_schema import (
    UserListResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)
from app.schemas.auth_schema import UserResponse
from app.services.admin_user_service import (
    AdminUserService,
    LastActiveAdminError,
    RoleChangeForbiddenError,
    StatusChangeForbiddenError,
    UserNotFoundError,
)

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


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def change_user_role(
    user_id: Annotated[int, Path(ge=1)],
    request: UserRoleUpdateRequest,
    db_session: Annotated[
        Session,
        Depends(get_db_session),
    ],
    current_admin: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN)),
    ],
) -> User:
    """Change a user role. Admin access only."""

    user_repository = UserRepository(db_session)
    admin_user_service = AdminUserService(user_repository)

    try:
        return admin_user_service.change_role(
            actor_id=current_admin.id,
            target_user_id=user_id,
            new_role=request.role,
        )

    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RoleChangeForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except LastActiveAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def change_user_status(
    user_id: Annotated[int, Path(ge=1)],
    request: UserStatusUpdateRequest,
    db_session: Annotated[
        Session,
        Depends(get_db_session),
    ],
    current_admin: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN)),
    ],
) -> User:
    """Activate or deactivate a user account. Admin only."""

    user_repository = UserRepository(db_session)
    admin_user_service = AdminUserService(user_repository)

    try:
        return admin_user_service.change_status(
            actor_id=current_admin.id,
            target_user_id=user_id,
            is_active=request.is_active,
        )

    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except StatusChangeForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except LastActiveAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
