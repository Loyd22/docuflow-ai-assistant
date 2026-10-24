"""Business logic for authorized original-document access."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.document_repository import get_document_by_id
from app.security.document_access_policy import DocumentAccessPolicy
from app.storage.file_storage import get_stored_file_path


class DocumentFileNotFoundError(Exception):
    """The requested document or its original file is missing."""


class DocumentFileAccessDeniedError(Exception):
    """The user does not have permission to access the file."""


class DocumentFileStorageError(Exception):
    """The stored filename or file location is invalid."""


@dataclass(frozen=True)
class AuthorizedDocumentFile:
    """Information needed to return an authorized document."""

    path: Path
    original_file_name: str
    mime_type: str


class DocumentFileAccessService:
    """Verify document access before retrieving an original file."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_authorized_file(
        self,
        *,
        document_id: int,
        current_user: User,
    ) -> AuthorizedDocumentFile:
        """Return original-file information if access is permitted."""

        # Find the document in PostgreSQL.
        document = get_document_by_id(
            self.database_session,
            document_id,
        )

        if document is None:
            raise DocumentFileNotFoundError("Document not found.")

        # Check user permissions before accessing the file.
        # Apply the same read permissions used by other document endpoints.
        if not DocumentAccessPolicy.can_read_document(
            document=document,
            current_user=current_user,
        ):
            raise DocumentFileAccessDeniedError(
                "You are not allowed to access this document."
            )

        # Use the internal filename, not the database file path.
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
