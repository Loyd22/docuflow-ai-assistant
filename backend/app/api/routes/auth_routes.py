from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_roles,
)
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: RegisterRequest,
    db_session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> User:
    """Register a new user account."""

    user_repository = UserRepository(db_session)
    auth_service = AuthService(user_repository)

    try:
        return auth_service.register(request)

    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    request: LoginRequest,
    db_session: Annotated[
        Session,
        Depends(get_db_session),
    ],
) -> TokenResponse:
    """Authenticate a user and return an access token."""

    user_repository = UserRepository(db_session)
    auth_service = AuthService(user_repository)

    try:
        access_token = auth_service.login(request)

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return TokenResponse(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_authenticated_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Return the currently authenticated user."""

    return current_user


@router.get(
    "/manager-test",
    response_model=UserResponse,
)
def manager_test(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.ADMIN,
            )
        ),
    ],
) -> User:
    """Temporary route for testing manager/admin authorization."""

    return current_user


@router.get(
    "/admin-test",
    response_model=UserResponse,
)
def admin_test(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN)),
    ],
) -> User:
    """Temporary route for testing admin-only authorization."""

    return current_user
