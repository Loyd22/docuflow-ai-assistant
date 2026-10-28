"""
Tests for application environment configuration.

Make sure unsafe settings are rejected before production starts.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

# Use dummy values instead of real credentials.
BASE_SETTINGS = {
    "database_url": "postgresql+psycopg://user:password@localhost:5432/test",
    "jwt_secret_key": "a-secure-example-secret-with-more-than-32-characters",
}


def create_test_settings(**overrides: object) -> Settings:
    """Create settings without reading the local .env file."""

    values = {
        **BASE_SETTINGS,
        **overrides,
    }

    return Settings(_env_file=None, **values)


def test_development_allows_debug() -> None:
    """Debug mode is allowed during local development."""

    settings = create_test_settings(
        app_env="development",
        app_debug=True,
    )

    assert settings.app_env == "development"
    assert settings.app_debug is True


def test_testing_environment_is_allowed() -> None:
    """The CI environment should load successfully."""

    settings = create_test_settings(
        app_env="testing",
        app_debug=False,
    )

    assert settings.app_env == "testing"


def test_production_rejects_debug_enabled() -> None:
    """Debug mode must never be enabled in production."""

    with pytest.raises(ValidationError, match="APP_DEBUG must be false"):
        create_test_settings(
            app_env="production",
            app_debug=True,
            cors_allowed_origins=["https://example.com"],
        )


def test_production_rejects_short_jwt_secret() -> None:
    """Reject weak JWT signing secrets."""

    with pytest.raises(ValidationError, match="Production JWT_SECRET_KEY"):
        create_test_settings(
            app_env="production",
            app_debug=False,
            jwt_secret_key="short-secret",
            cors_allowed_origins=["https://example.com"],
        )


def test_production_rejects_http_origin() -> None:
    """Production browsers must use an HTTPS frontend origin."""

    with pytest.raises(ValidationError, match="must use HTTPS"):
        create_test_settings(
            app_env="production",
            app_debug=False,
            cors_allowed_origins=["http://example.com"],
        )


def test_production_rejects_empty_cors_origins() -> None:
    """Production requires at least one frontend origin."""

    with pytest.raises(ValidationError, match="cannot be empty"):
        create_test_settings(
            app_env="production",
            app_debug=False,
            cors_allowed_origins=[],
        )


def test_production_accepts_valid_configuration() -> None:
    """A valid production configuration should load."""

    settings = create_test_settings(
        app_env="production",
        app_debug=False,
        cors_allowed_origins=["https://example.com"],
    )

    assert settings.app_env == "production"
    assert settings.app_debug is False
    assert settings.cors_allowed_origins == ["https://example.com"]


def test_invalid_environment_is_rejected() -> None:
    """Only supported environment names are allowed."""

    with pytest.raises(ValidationError):
        create_test_settings(
            app_env="invalid-environment",
        )


def test_test_database_url_is_optional() -> None:
    """Production startup should not require a test database."""

    settings = create_test_settings(
        app_env="production",
        app_debug=False,
        cors_allowed_origins=["https://example.com"],
        test_database_url=None,
    )

    assert settings.test_database_url is None
