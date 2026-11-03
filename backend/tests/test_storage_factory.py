"""Tests for storage provider selection."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.storage import factory
from app.storage.local_storage import LocalDocumentStorage


def test_storage_factory_returns_local_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Local configuration should select the local adapter."""

    monkeypatch.setattr(
        factory.settings,
        "storage_provider",
        "local",
    )

    storage = factory.get_document_storage()

    assert isinstance(storage, LocalDocumentStorage)


def test_settings_reject_unsupported_storage_provider() -> None:
    """An unsupported provider must fail configuration validation."""

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="sqlite:///test.db",
            jwt_secret_key="a-test-secret",
            storage_provider="unknown",
        )


def test_storage_factory_returns_supabase_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Select Supabase Storage when configured."""

    from unittest.mock import MagicMock, patch

    from app.storage.supabase_storage import SupabaseDocumentStorage

    monkeypatch.setattr(factory.settings, "storage_provider", "supabase")
    monkeypatch.setattr(
        factory.settings,
        "supabase_url",
        "https://example.supabase.co",
    )
    monkeypatch.setattr(
        factory.settings,
        "supabase_secret_key",
        "dummy-test-key",
    )
    monkeypatch.setattr(
        factory.settings,
        "supabase_storage_bucket",
        "docuflow-documents",
    )

    mock_client = MagicMock()

    with patch(
        "supabase.create_client",
        return_value=mock_client,
    ) as mock_create_client:
        storage = factory.get_document_storage()

    assert isinstance(storage, SupabaseDocumentStorage)

    mock_create_client.assert_called_once_with(
        "https://example.supabase.co",
        "dummy-test-key",
    )

    mock_client.storage.from_.assert_called_once_with("docuflow-documents")


def test_supabase_configuration_requires_credentials() -> None:
    """Reject Supabase configuration without credentials."""

    with pytest.raises(
        ValidationError,
        match="SUPABASE_SECRET_KEY",
    ):
        Settings(
            _env_file=None,
            database_url="sqlite:///test.db",
            jwt_secret_key="dummy-test-secret",
            storage_provider="supabase",
            supabase_url="https://example.supabase.co",
            supabase_secret_key=None,
        )


def test_local_storage_does_not_require_supabase_credentials() -> None:
    """Local storage works without cloud credentials."""

    settings = Settings(
        _env_file=None,
        database_url="sqlite:///test.db",
        jwt_secret_key="dummy-test-secret",
        storage_provider="local",
        supabase_url=None,
        supabase_secret_key=None,
    )

    assert settings.storage_provider == "local"


def test_explicit_local_provider_ignores_default_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Historical local documents use local storage."""

    from app.storage.local_storage import LocalDocumentStorage

    monkeypatch.setattr(
        factory.settings,
        "storage_provider",
        "supabase",
    )

    storage = factory.get_document_storage_for_provider("local")

    assert isinstance(storage, LocalDocumentStorage)


def test_explicit_supabase_provider_ignores_local_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cloud documents use Supabase even if local is the default."""

    from unittest.mock import MagicMock, patch

    from app.storage.supabase_storage import SupabaseDocumentStorage

    monkeypatch.setattr(
        factory.settings,
        "storage_provider",
        "local",
    )
    monkeypatch.setattr(
        factory.settings,
        "supabase_url",
        "https://example.supabase.co",
    )
    monkeypatch.setattr(
        factory.settings,
        "supabase_secret_key",
        "dummy-test-key",
    )

    with patch(
        "supabase.create_client",
        return_value=MagicMock(),
    ):
        storage = factory.get_document_storage_for_provider("supabase")

    assert isinstance(storage, SupabaseDocumentStorage)


def test_unknown_storage_provider_is_rejected() -> None:
    """Reject unknown providers instead of using a fallback."""

    with pytest.raises(
        ValueError,
        match="Unsupported storage provider",
    ):
        factory.get_document_storage_for_provider("unknown")
