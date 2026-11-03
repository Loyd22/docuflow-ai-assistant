"""Tests for the Supabase document storage adapter."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from storage3.exceptions import StorageApiError

from app.storage.supabase_storage import SupabaseDocumentStorage


@pytest.fixture
def storage() -> tuple[SupabaseDocumentStorage, MagicMock]:
    """Create storage with a mocked Supabase client."""

    client = MagicMock()
    bucket = client.storage.from_.return_value

    adapter = SupabaseDocumentStorage(
        client=client,
        bucket_name="docuflow-documents",
    )

    client.storage.from_.assert_called_once_with("docuflow-documents")

    return adapter, bucket


def test_save_uploads_document(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
) -> None:
    """Upload a document without allowing overwrites."""

    adapter, bucket = storage
    source = BytesIO(b"Sample PDF content")

    key = adapter.save(
        source,
        "invoice.pdf",
    )

    assert key == "invoice.pdf"

    bucket.upload.assert_called_once_with(
        path="invoice.pdf",
        file=b"Sample PDF content",
        file_options={
            "content-type": "application/pdf",
            "upsert": "false",
        },
    )


def test_download_creates_local_file(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
    tmp_path: Path,
) -> None:
    """Downloaded bytes must match the stored object."""

    adapter, bucket = storage
    bucket.download.return_value = b"Private document"

    destination = tmp_path / "downloaded.txt"

    adapter.download_to_path(
        "document.txt",
        destination,
    )

    bucket.download.assert_called_once_with("document.txt")
    assert destination.read_bytes() == b"Private document"


def test_delete_removes_object(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
) -> None:
    """Delete the specified object from the bucket."""

    adapter, bucket = storage

    adapter.delete("invoice.pdf")

    bucket.remove.assert_called_once_with(["invoice.pdf"])


@pytest.mark.parametrize(
    "invalid_key",
    [
        "../secret.txt",
        "folder/file.txt",
        r"..\secret.txt",
        "",
        ".",
        "..",
    ],
)
def test_rejects_invalid_storage_keys(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
    invalid_key: str,
) -> None:
    """Reject keys that are not simple filenames."""

    adapter, bucket = storage

    with pytest.raises(ValueError, match="Invalid stored file name"):
        adapter.save(
            BytesIO(b"Private content"),
            invalid_key,
        )

    bucket.upload.assert_not_called()


def test_download_does_not_overwrite_existing_file(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
    tmp_path: Path,
) -> None:
    """An existing local destination must remain unchanged."""

    adapter, bucket = storage
    bucket.download.return_value = b"Replacement content"

    destination = tmp_path / "existing.txt"
    destination.write_bytes(b"Original content")

    with pytest.raises(FileExistsError):
        adapter.download_to_path(
            "document.txt",
            destination,
        )

    assert destination.read_bytes() == b"Original content"


def test_download_failure_does_not_create_file(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
    tmp_path: Path,
) -> None:
    """A failed cloud download must not create a local file."""

    adapter, bucket = storage

    bucket.download.side_effect = OSError("Cloud storage unavailable")

    destination = tmp_path / "failed.txt"

    with pytest.raises(OSError, match="Cloud storage unavailable"):
        adapter.download_to_path(
            "document.txt",
            destination,
        )

    assert not destination.exists()


@pytest.mark.parametrize(
    "error_code",
    [
        "NoSuchKey",
        "not_found",
    ],
)
def test_download_missing_object_raises_file_not_found(
    storage: tuple[SupabaseDocumentStorage, MagicMock],
    tmp_path: Path,
    error_code: str,
) -> None:
    """Translate supported missing-object errors into FileNotFoundError."""

    adapter, bucket = storage

    # Simulate different missing-object errors from Supabase.
    bucket.download.side_effect = StorageApiError(
        "Object not found",
        error_code,
        404,
    )

    destination = tmp_path / "missing.txt"

    with pytest.raises(
        FileNotFoundError,
        match="Original document file not found",
    ):
        adapter.download_to_path(
            "missing.txt",
            destination,
        )

    # Failed downloads must not leave temporary files behind.
    assert not destination.exists()
