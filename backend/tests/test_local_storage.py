"""Tests for the local document storage adapter."""

from io import BytesIO
from pathlib import Path

import pytest

from app.storage import file_storage
from app.storage.local_storage import LocalDocumentStorage


@pytest.fixture
def storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> LocalDocumentStorage:
    """Use a temporary directory instead of real uploads."""

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        tmp_path,
    )

    return LocalDocumentStorage()


def test_save_creates_file(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """Saving a document creates a file with its content."""

    key = storage.save(
        BytesIO(b"Sample document"),
        "document.txt",
    )

    assert key == "document.txt"
    assert (tmp_path / key).read_bytes() == b"Sample document"


def test_download_copies_file(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """A stored document can be copied to a new path."""

    key = storage.save(
        BytesIO(b"Invoice content"),
        "invoice.txt",
    )

    destination = tmp_path.parent / "downloaded-invoice.txt"

    storage.download_to_path(key, destination)

    assert destination.read_bytes() == b"Invoice content"


def test_delete_removes_file(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """Deleting a document removes the stored file."""

    key = storage.save(
        BytesIO(b"Temporary file"),
        "temporary.txt",
    )

    storage.delete(key)

    assert not (tmp_path / key).exists()


@pytest.mark.parametrize(
    "invalid_name",
    [
        "../secret.txt",
        "folder/file.txt",
        r"..\secret.txt",
        "",
        ".",
        "..",
    ],
)
def test_save_rejects_invalid_names(
    storage: LocalDocumentStorage,
    invalid_name: str,
) -> None:
    """Storage keys cannot escape the uploads directory."""

    with pytest.raises(ValueError, match="Invalid stored file name"):
        storage.save(
            BytesIO(b"Private content"),
            invalid_name,
        )


def test_save_does_not_overwrite_existing_file(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """An existing document must not be overwritten."""

    storage.save(
        BytesIO(b"Original content"),
        "existing.txt",
    )

    with pytest.raises(FileExistsError):
        storage.save(
            BytesIO(b"Replacement content"),
            "existing.txt",
        )

    assert (tmp_path / "existing.txt").read_bytes() == b"Original content"


def test_download_rejects_missing_file(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """Downloading an unknown file raises an error."""

    with pytest.raises(FileNotFoundError):
        storage.download_to_path(
            "missing.txt",
            tmp_path / "download.txt",
        )


def test_save_removes_partial_file_on_failure(
    storage: LocalDocumentStorage,
    tmp_path: Path,
) -> None:
    """A failed upload must not leave incomplete content."""

    class FailingStream(BytesIO):
        def read(self, size: int = -1) -> bytes:
            if self.tell() > 0:
                raise OSError("Simulated read failure")

            return super().read(4)

    with pytest.raises(OSError, match="Simulated read failure"):
        storage.save(
            FailingStream(b"Partially written content"),
            "incomplete.txt",
        )

    assert not (tmp_path / "incomplete.txt").exists()
