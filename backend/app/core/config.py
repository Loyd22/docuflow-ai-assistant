"""
Central application configuration.

This file reads environment variables and makes them available
to the rest of the backend through one settings object.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Defines all configuration values required by DocuFlow."""

    app_name: str = "DocuFlow AI"
    app_env: str = "development"
    app_debug: bool = True

    postgres_host: str = "localhost"
    postgres_port: int = 5434
    postgres_db: str = "docuflow_db"
    postgres_user: str = "docuflow_user"
    postgres_password: str = "docuflow_password"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    test_database_url: str
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"

    database_url: str

    # Tell Pydantic to read values from backend/.env.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache one Settings object.

    Caching prevents the application from repeatedly reading
    the same environment file.
    """

    return Settings()


settings = get_settings()
