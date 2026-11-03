"""Local filesystem implementation of document storage."""

from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO

from app.storage import file_storage


class LocalDocumentStorage:
    """Store documents in the local uploads directory."""

    @staticmethod
    def _validate_storage_key(storage_key: str) -> None:
        """Reject unsafe filenames and directory traversal."""

        if (
            not storage_key
            or storage_key != Path(storage_key).name
            or "/" in storage_key
            or "\\" in storage_key
            or storage_key in {".", ".."}
        ):
            raise ValueError("Invalid stored file name.")

    def save(
        self,
        source: BinaryIO,
        stored_name: str,
    ) -> str:
        """Save a document and remove incomplete files on failure."""

        self._validate_storage_key(stored_name)
        file_storage.ensure_upload_directory_exists()

        destination = file_storage.UPLOAD_DIRECTORY / stored_name

        # Only delete the file if this operation created it.
        created = False

        try:
            # Exclusive creation prevents overwriting existing files.
            with destination.open("xb") as output:
                created = True
                source.seek(0)
                copyfileobj(source, output, length=1024 * 1024)

        except Exception:
            # The with block has closed the file before cleanup.
            if created:
                destination.unlink(missing_ok=True)
            raise

        return stored_name

    def download_to_path(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        """Copy a stored document to a new local path."""

        source_path = file_storage.get_stored_file_path(storage_key)

        created = False

        try:
            # Open source and destination in one with statement.
            with (
                source_path.open("rb") as source,
                destination.open("xb") as output,
            ):
                created = True
                copyfileobj(source, output, length=1024 * 1024)

        except Exception:
            # Remove only the incomplete destination created by us.
            if created:
                destination.unlink(missing_ok=True)
            raise

    def delete(self, storage_key: str) -> None:
        """Delete a stored document."""

        source_path = file_storage.get_stored_file_path(storage_key)
        source_path.unlink()
