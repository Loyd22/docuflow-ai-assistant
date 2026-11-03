"""Tests for storage-backed authorized document access."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.document_file_access_service import (
    DocumentFileAccessDeniedError,
    DocumentFileAccessService,
    DocumentFileNotFoundError,
)


def make_document() -> SimpleNamespace:
    """Create document information needed by the access service."""

    return SimpleNamespace(
        id=25,
        stored_file_name="stored-document.txt",
        original_file_name="invoice.txt",
        mime_type="text/plain",
    )


def test_authorized_user_can_retrieve_stored_file() -> None:
    """Authorized users can retrieve files through storage."""

    database_session = MagicMock()
    storage = MagicMock()
    current_user = MagicMock()
    document = make_document()

    downloaded_paths: list[Path] = []

    def fake_download(storage_key: str, destination: Path) -> None:
        assert storage_key == "stored-document.txt"
        downloaded_paths.append(destination)
        destination.write_bytes(b"Private invoice content")

    storage.download_to_path.side_effect = fake_download

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
            storage=storage,
        )

        result = service.get_authorized_file(
            document_id=25,
            current_user=current_user,
        )

    try:
        assert result.path.read_bytes() == b"Private invoice content"
        assert result.original_file_name == "invoice.txt"
        assert result.path.suffix == ".txt"
        assert len(downloaded_paths) == 1
    finally:
        result.cleanup()

    assert not downloaded_paths[0].exists()


def test_unauthorized_user_never_accesses_storage() -> None:
    """Reject unauthorized users before accessing storage."""

    database_session = MagicMock()
    storage = MagicMock()
    current_user = MagicMock()

    with (
        patch(
            "app.services.document_file_access_service.get_document_by_id",
            return_value=make_document(),
        ),
        patch(
            "app.services.document_file_access_service."
            "DocumentAccessPolicy.can_read_document",
            return_value=False,
        ),
        pytest.raises(DocumentFileAccessDeniedError),
    ):
        service = DocumentFileAccessService(
            database_session,
            storage=storage,
        )

        service.get_authorized_file(
            document_id=25,
            current_user=current_user,
        )

    storage.download_to_path.assert_not_called()


def test_missing_cloud_object_returns_not_found() -> None:
    """Missing objects return a document-not-found error."""

    database_session = MagicMock()
    storage = MagicMock()
    current_user = MagicMock()

    storage.download_to_path.side_effect = FileNotFoundError("Object not found")

    with (
        patch(
            "app.services.document_file_access_service.get_document_by_id",
            return_value=make_document(),
        ),
        patch(
            "app.services.document_file_access_service."
            "DocumentAccessPolicy.can_read_document",
            return_value=True,
        ),
        pytest.raises(DocumentFileNotFoundError),
    ):
        service = DocumentFileAccessService(
            database_session,
            storage=storage,
        )

        service.get_authorized_file(
            document_id=25,
            current_user=current_user,
        )
