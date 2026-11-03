"""Business logic for authorized original-document access."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.document_repository import get_document_by_id
from app.security.document_access_policy import DocumentAccessPolicy
from app.storage.base import DocumentStorage
from app.storage.file_storage import get_stored_file_path


class DocumentFileNotFoundError(Exception):
    """The requested document or original file is missing."""


class DocumentFileAccessDeniedError(Exception):
    """The user does not have permission to access the file."""


class DocumentFileStorageError(Exception):
    """The original document cannot be retrieved safely."""


@dataclass(frozen=True)
class AuthorizedDocumentFile:
    """Information needed to return an authorized document."""

    path: Path
    original_file_name: str
    mime_type: str
    temporary_directory: TemporaryDirectory[str] | None = None

    def cleanup(self) -> None:
        """Remove downloaded temporary files when no longer needed."""

        if self.temporary_directory is not None:
            self.temporary_directory.cleanup()


class DocumentFileAccessService:
    """Verify permissions before retrieving original documents."""

    def __init__(
        self,
        database_session: Session,
        storage: DocumentStorage | None = None,
        storage_resolver: Callable[[str], DocumentStorage] | None = None,
    ) -> None:
        self.database_session = database_session
        self.storage = storage
        self.storage_resolver = storage_resolver

    def get_authorized_file(
        self,
        *,
        document_id: int,
        current_user: User,
    ) -> AuthorizedDocumentFile:
        """Retrieve an original file only after authorization."""

        document = get_document_by_id(
            self.database_session,
            document_id,
        )

        if document is None:
            raise DocumentFileNotFoundError("Document not found.")

        # Always check permission before accessing storage.
        if not DocumentAccessPolicy.can_read_document(
            document=document,
            current_user=current_user,
        ):
            raise DocumentFileAccessDeniedError(
                "You are not allowed to access this document."
            )

        # Preserve the historical local-file access behavior.
        if self.storage is None and self.storage_resolver is None:
            try:
                file_path = get_stored_file_path(
                    document.stored_file_name,
                )

            except FileNotFoundError as error:
                raise DocumentFileNotFoundError(
                    "Original document file not found."
                ) from error

            except ValueError as error:
                raise DocumentFileStorageError(
                    "Invalid original document storage path."
                ) from error

            return AuthorizedDocumentFile(
                path=file_path,
                original_file_name=document.original_file_name,
                mime_type=document.mime_type,
            )

        # Use a temporary directory for retrieved documents.
        temporary_directory = TemporaryDirectory()

        try:
            extension = Path(document.stored_file_name).suffix.lower()

            if extension not in {".pdf", ".docx", ".txt"}:
                raise DocumentFileStorageError("Invalid original document extension.")

            # Explicit adapters remain supported for existing tests.
            document_storage = self.storage

            if document_storage is None:
                assert self.storage_resolver is not None

                # Resolve the provider saved with this document.
                document_storage = self.storage_resolver(document.storage_provider)

            file_path = Path(temporary_directory.name) / f"document{extension}"

            # Retrieve the file only after authorization.
            document_storage.download_to_path(
                document.stored_file_name,
                file_path,
            )

            return AuthorizedDocumentFile(
                path=file_path,
                original_file_name=document.original_file_name,
                mime_type=document.mime_type,
                temporary_directory=temporary_directory,
            )

        except Exception as error:
            # Clean up temporary files after retrieval failures.
            temporary_directory.cleanup()

            if isinstance(error, FileNotFoundError):
                raise DocumentFileNotFoundError(
                    "Original document file not found."
                ) from error

            if isinstance(error, DocumentFileStorageError):
                raise

            raise DocumentFileStorageError(
                "Original document storage is unavailable."
            ) from error
