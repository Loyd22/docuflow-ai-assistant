"""
Central application configuration.

Loads environment variables and validates settings before
the application starts.
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for development, testing, and production."""

    app_name: str = "DocuFlow AI"
    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = True

    # Frontend origins allowed to call our backend.
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    postgres_host: str = "localhost"
    postgres_port: int = 5434
    postgres_db: str = "docuflow_db"
    postgres_user: str = "docuflow_user"
    postgres_password: str = "docuflow_password"

    database_url: str
    test_database_url: str | None = None

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Reject unsafe configuration in production."""

        if self.app_env != "production":
            return self

        # Never enable debug behavior in production.
        if self.app_debug:
            raise ValueError("APP_DEBUG must be false in production.")

        # Require a reasonably long JWT signing secret.
        if (
            len(self.jwt_secret_key) < 32
            or self.jwt_secret_key == "replace-with-a-secure-secret"
        ):
            raise ValueError("Production JWT_SECRET_KEY must be a secure secret.")

        # Production must explicitly allow HTTPS frontend origins.
        if not self.cors_allowed_origins:
            raise ValueError("Production CORS_ALLOWED_ORIGINS cannot be empty.")

        for origin in self.cors_allowed_origins:
            if not origin.startswith("https://"):
                raise ValueError("Production CORS origins must use HTTPS.")

            if "*" in origin:
                raise ValueError("Wildcard CORS origins are not allowed in production.")

        return self


@lru_cache
def get_settings() -> Settings:
    """Create and cache the application settings."""

    return Settings()


settings = get_settings()
