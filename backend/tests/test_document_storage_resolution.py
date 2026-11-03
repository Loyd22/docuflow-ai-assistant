"""Tests for authorized document-specific storage resolution."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_file_access_service import (
    DocumentFileAccessDeniedError,
    DocumentFileAccessService,
    DocumentFileStorageError,
)


def make_document(provider: str = "local") -> MagicMock:
    """Create a document with storage metadata."""

    document = MagicMock()
    document.id = 10
    document.stored_file_name = "stored-document.txt"
    document.original_file_name = "document.txt"
    document.mime_type = "text/plain"
    document.storage_provider = provider
    return document


@pytest.mark.parametrize("provider", ["local", "supabase"])
def test_authorized_file_uses_document_provider(
    provider: str,
) -> None:
    """Retrieve files using the provider saved in PostgreSQL."""

    database_session = MagicMock()
    current_user = MagicMock()
    document = make_document(provider)

    storage = MagicMock()
    storage.download_to_path.side_effect = lambda key, destination: (
        destination.write_bytes(b"Original document")
    )

    resolver = MagicMock(return_value=storage)

    with (
        patch(
            "app.services.document_file_access_service.get_document_by_id",
            return_value=document,
        ),
        patch(
            "app.services.document_file_access_service."
            "DocumentAccessPolicy.can_read_document",
            return_value=True,
        ),
    ):
        service = DocumentFileAccessService(
            database_session,
            storage_resolver=resolver,
        )

        original_file = service.get_authorized_file(
            document_id=10,
            current_user=current_user,
        )

    try:
        resolver.assert_called_once_with(provider)

        assert original_file.path.read_bytes() == (b"Original document")

        storage.download_to_path.assert_called_once()
        assert original_file.original_file_name == "document.txt"

    finally:
        original_file.cleanup()


def test_unauthorized_user_never_resolves_storage() -> None:
    """Denied access must not initialize or contact storage."""

    database_session = MagicMock()
    current_user = MagicMock()
    document = make_document("supabase")
    resolver = MagicMock()

    with (
        patch(
            "app.services.document_file_access_service.get_document_by_id",
            return_value=document,
        ),
        patch(
            "app.services.document_file_access_service."
            "DocumentAccessPolicy.can_read_document",
            return_value=False,
        ),
    ):
        service = DocumentFileAccessService(
            database_session,
            storage_resolver=resolver,
        )

        with pytest.raises(DocumentFileAccessDeniedError):
            service.get_authorized_file(
                document_id=10,
                current_user=current_user,
            )

    resolver.assert_not_called()


def test_storage_resolution_failure_is_handled() -> None:
    """Provider initialization failures become storage errors."""

    database_session = MagicMock()
    current_user = MagicMock()
    document = make_document("supabase")

    resolver = MagicMock(side_effect=ValueError("Missing Supabase configuration"))

    with (
        patch(
            "app.services.document_file_access_service.get_document_by_id",
            return_value=document,
        ),
        patch(
            "app.services.document_file_access_service."
            "DocumentAccessPolicy.can_read_document",
            return_value=True,
        ),
    ):
        service = DocumentFileAccessService(
            database_session,
            storage_resolver=resolver,
        )

        with pytest.raises(
            DocumentFileStorageError,
            match="Original document storage is unavailable",
        ):
            service.get_authorized_file(
                document_id=10,
                current_user=current_user,
            )

    resolver.assert_called_once_with("supabase")
