"""Supabase implementation of document storage."""

from pathlib import Path
from typing import Any, BinaryIO, ClassVar

from storage3.exceptions import StorageApiError


class SupabaseDocumentStorage:
    """Store documents in a private Supabase Storage bucket."""

    CONTENT_TYPES: ClassVar[dict[str, str]] = {
        ".pdf": "application/pdf",
        ".docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        ".txt": "text/plain",
    }

    def __init__(
        self,
        client: Any,
        bucket_name: str = "docuflow-documents",
    ) -> None:
        """Use an existing Supabase client and private bucket."""

        self.bucket = client.storage.from_(bucket_name)

    @staticmethod
    def _validate_storage_key(storage_key: str) -> None:
        """Reject paths and unsafe object names."""

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
        """Upload a document without overwriting existing objects."""

        self._validate_storage_key(stored_name)

        extension = Path(stored_name).suffix.lower()

        if extension not in self.CONTENT_TYPES:
            raise ValueError("Unsupported document extension.")

        # Start reading the uploaded file from the beginning.
        # Read the file from the beginning.
        source.seek(0)
        content = source.read()

        try:
            # Upload bytes supported by the Supabase SDK.
            self.bucket.upload(
                path=stored_name,
                file=content,
                file_options={
                    "content-type": self.CONTENT_TYPES[extension],
                    "upsert": "false",
                },
            )

        except StorageApiError as error:
            # Convert known duplicate-object errors.
            if error.code in {
                "KeyAlreadyExists",
                "ResourceAlreadyExists",
                "already_exists",
            }:
                raise FileExistsError("Document already exists in storage.") from error

            # Preserve other errors without deleting remote objects.
            raise

        return stored_name

    def download_to_path(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        """Download a private object and handle missing files."""

        self._validate_storage_key(storage_key)

        try:
            # Retrieve the original document bytes.
            content = self.bucket.download(storage_key)

        except StorageApiError as error:
            # Supabase may return either its current or legacy error code.
            if error.code in {"NoSuchKey", "not_found"}:
                raise FileNotFoundError("Original document file not found.") from error

            # Preserve unrelated cloud storage failures.
            raise

        created = False

        try:
            # Do not overwrite an existing local file.
            with destination.open("xb") as output:
                created = True
                output.write(content)

        except Exception:
            # Remove an incomplete file created by this call.
            if created:
                destination.unlink(missing_ok=True)
            raise

    def delete(self, storage_key: str) -> None:
        """Remove a stored document from the private bucket."""

        self._validate_storage_key(storage_key)

        self.bucket.remove([storage_key])
