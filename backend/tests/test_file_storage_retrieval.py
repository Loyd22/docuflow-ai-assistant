"""Tests for secure original-file retrieval."""

from pathlib import Path

import pytest

from app.storage import file_storage


def test_get_stored_file_path_returns_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An uploaded file can be found inside the storage directory."""

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        tmp_path,
    )

    stored_file = tmp_path / "example.txt"
    stored_file.write_text("Sample invoice", encoding="utf-8")

    result = file_storage.get_stored_file_path("example.txt")

    assert result == stored_file.resolve()


@pytest.mark.parametrize(
    "stored_file_name",
    [
        "../secret.txt",
        "../../secret.txt",
        "folder/example.txt",
        r"..\secret.txt",
        "",
    ],
)
def test_get_stored_file_path_rejects_invalid_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stored_file_name: str,
) -> None:
    """A caller cannot pass a path instead of a stored filename."""

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        tmp_path,
    )

    with pytest.raises(ValueError, match="Invalid stored file name"):
        file_storage.get_stored_file_path(stored_file_name)


def test_get_stored_file_path_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing files are reported safely."""

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        file_storage.get_stored_file_path("missing.pdf")


def test_get_stored_file_path_rejects_symlink_outside_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink cannot point to a file outside the upload directory."""

    upload_directory = tmp_path / "uploads"
    upload_directory.mkdir()

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("Private data", encoding="utf-8")

    symlink = upload_directory / "linked.txt"

    try:
        symlink.symlink_to(outside_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable in this environment.")

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        upload_directory,
    )

    with pytest.raises(ValueError, match="Invalid stored file path"):
        file_storage.get_stored_file_path("linked.txt")
