from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.enums import UserRole


class RegisterRequest(BaseModel):
    """Data required to create a new user account."""

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Credentials required to authenticate a user."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Safe user information that may be returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    """JWT access token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
