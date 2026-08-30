from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.services.document_service import (
    MAX_FILE_SIZE_BYTES,
    upload_document,
)


def make_upload_file(
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
) -> UploadFile:
    """Create an UploadFile for service-layer tests."""

    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers={"content-type": content_type},
    )


def test_upload_document_success() -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"test document content",
    )

    fake_saved_path = Path("uploads/test-file.pdf")

    fake_document = MagicMock()

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="test-file.pdf",
        ),
        patch(
            "app.services.document_service.save_uploaded_file",
            return_value=fake_saved_path,
        ),
        patch(
            "app.services.document_service.validate_file_size",
            return_value=21,
        ),
        patch(
            "app.services.document_service.create_document",
            return_value=fake_document,
        ) as create_document_mock,
    ):
        result = upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert result is fake_document

    create_document_mock.assert_called_once_with(
        database_session,
        uploaded_by=1,
        original_file_name="invoice.pdf",
        stored_file_name="test-file.pdf",
        file_path=str(fake_saved_path),
        mime_type="application/pdf",
        file_size=21,
    )


def test_upload_document_rejects_unsupported_extension() -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="malware.exe",
        content=b"dangerous content",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )


def test_upload_document_rejects_empty_file(tmp_path: Path) -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="empty.pdf",
        content=b"",
    )

    saved_path = tmp_path / "empty.pdf"
    saved_path.write_bytes(b"")

    with (
        patch(
            "app.services.document_service.save_uploaded_file",
            return_value=saved_path,
        ),
        pytest.raises(
            ValueError,
            match="cannot be empty",
        ),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert not saved_path.exists()


def test_upload_document_rejects_oversized_file(
    tmp_path: Path,
) -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="large.pdf",
        content=b"test",
    )

    saved_path = tmp_path / "large.pdf"

    saved_path.write_bytes(b"x" * (MAX_FILE_SIZE_BYTES + 1))

    with (
        patch(
            "app.services.document_service.save_uploaded_file",
            return_value=saved_path,
        ),
        pytest.raises(
            ValueError,
            match="10 MB",
        ),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert not saved_path.exists()


def test_upload_document_deletes_file_when_database_fails(
    tmp_path: Path,
) -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"test document",
    )

    saved_path = tmp_path / "invoice.pdf"
    saved_path.write_bytes(b"test document")

    with (
        patch(
            "app.services.document_service.save_uploaded_file",
            return_value=saved_path,
        ),
        patch(
            "app.services.document_service.create_document",
            side_effect=SQLAlchemyError("database failure"),
        ),
        pytest.raises(SQLAlchemyError),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert not saved_path.exists()
    database_session.rollback.assert_called_once()
