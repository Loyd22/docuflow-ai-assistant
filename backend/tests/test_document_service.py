from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.db.enums import AuditAction, AuditEntityType
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
    fake_document.id = 25
    fake_document.original_file_name = "invoice.pdf"
    fake_document.mime_type = "application/pdf"
    fake_document.file_size = 21

    mock_audit_log_service = MagicMock()

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
        patch(
            "app.services.document_service.AuditLogService",
            return_value=mock_audit_log_service,
        ) as audit_log_service_mock,
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
        storage_provider="local",
        commit=False,
    )

    audit_log_service_mock.assert_called_once_with(
        database_session=database_session,
    )

    mock_audit_log_service.record_event.assert_called_once_with(
        user_id=1,
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type=AuditEntityType.DOCUMENT,
        entity_id=25,
        event_metadata={
            "original_file_name": "invoice.pdf",
            "mime_type": "application/pdf",
            "file_size": 21,
        },
        commit=False,
    )

    database_session.commit.assert_called_once()
    database_session.rollback.assert_not_called()


def test_upload_document_rejects_unsupported_extension() -> None:
    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="malware.exe",
        content=b"dangerous content",
    )

    with (
        patch(
            "app.services.document_service.AuditLogService",
        ) as audit_log_service_mock,
        pytest.raises(
            ValueError,
            match="Unsupported file type",
        ),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    audit_log_service_mock.assert_not_called()


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
        patch(
            "app.services.document_service.AuditLogService",
        ) as audit_log_service_mock,
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
    audit_log_service_mock.assert_not_called()


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
        patch(
            "app.services.document_service.AuditLogService",
        ) as audit_log_service_mock,
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
    audit_log_service_mock.assert_not_called()


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
        patch(
            "app.services.document_service.AuditLogService",
        ) as audit_log_service_mock,
        pytest.raises(SQLAlchemyError),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert not saved_path.exists()
    database_session.rollback.assert_called_once()
    audit_log_service_mock.assert_not_called()


def test_upload_document_rolls_back_when_audit_fails(
    tmp_path: Path,
) -> None:
    """An audit failure rolls back the upload and deletes its file."""

    database_session = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"test document",
    )

    saved_path = tmp_path / "invoice.pdf"
    saved_path.write_bytes(b"test document")

    fake_document = MagicMock()
    fake_document.id = 25

    mock_audit_service = MagicMock()
    mock_audit_service.record_event.side_effect = SQLAlchemyError(
        "audit database failure"
    )

    with (
        patch(
            "app.services.document_service.save_uploaded_file",
            return_value=saved_path,
        ),
        patch(
            "app.services.document_service.validate_file_size",
            return_value=13,
        ),
        patch(
            "app.services.document_service.create_document",
            return_value=fake_document,
        ) as create_document_mock,
        patch(
            "app.services.document_service.AuditLogService",
            return_value=mock_audit_service,
        ),
        pytest.raises(SQLAlchemyError, match="audit database failure"),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
        )

    assert not saved_path.exists()

    create_document_mock.assert_called_once()
    assert create_document_mock.call_args.kwargs["commit"] is False

    mock_audit_service.record_event.assert_called_once()
    assert mock_audit_service.record_event.call_args.kwargs["commit"] is False

    database_session.rollback.assert_called_once()
    database_session.commit.assert_not_called()


def test_upload_document_uses_injected_storage() -> None:
    """Upload documents through the provided storage adapter."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    storage.save.return_value = "stored-invoice.pdf"

    fake_document = MagicMock()
    fake_document.id = 25

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="stored-invoice.pdf",
        ),
        patch(
            "app.services.document_service.create_document",
            return_value=fake_document,
        ) as create_document_mock,
        patch(
            "app.services.document_service.AuditLogService",
        ),
    ):
        result = upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
        )

    assert result is fake_document

    storage.save.assert_called_once_with(
        uploaded_file.file,
        "stored-invoice.pdf",
    )

    create_document_mock.assert_called_once()
    database_session.commit.assert_called_once()


def test_injected_storage_deleted_when_database_fails() -> None:
    """Remove an uploaded object if database creation fails."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    storage.save.return_value = "stored-invoice.pdf"

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="stored-invoice.pdf",
        ),
        patch(
            "app.services.document_service.create_document",
            side_effect=SQLAlchemyError("Database failure"),
        ),
        pytest.raises(SQLAlchemyError, match="Database failure"),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
        )

    storage.save.assert_called_once_with(
        uploaded_file.file,
        "stored-invoice.pdf",
    )

    storage.delete.assert_called_once_with("stored-invoice.pdf")

    database_session.rollback.assert_called_once()
    database_session.commit.assert_not_called()


def test_injected_storage_failure_does_not_create_document() -> None:
    """A storage failure must stop database persistence."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    storage.save.side_effect = OSError("Storage unavailable")

    with (
        patch(
            "app.services.document_service.create_document",
        ) as create_document_mock,
        patch(
            "app.services.document_service.AuditLogService",
        ) as audit_service_mock,
        pytest.raises(OSError, match="Storage unavailable"),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
        )

    create_document_mock.assert_not_called()
    audit_service_mock.assert_not_called()

    database_session.commit.assert_not_called()


def test_database_error_preserved_when_storage_cleanup_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keep the database error even when deleting the file fails."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    # The cloud upload succeeds.
    storage.save.return_value = "stored-invoice.pdf"

    # Deleting the cloud object fails during recovery.
    # Simulate an SDK exception containing a sensitive credential.
    sensitive_marker = "FAKE_SECRET_DO_NOT_LOG_123"

    storage.delete.side_effect = OSError(
        f"Supabase cleanup failed: authorization=Bearer {sensitive_marker}"
    )

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="stored-invoice.pdf",
        ),
        patch(
            "app.services.document_service.create_document",
            side_effect=SQLAlchemyError("Database insert failed"),
        ),
        pytest.raises(
            SQLAlchemyError,
            match="Database insert failed",
        ),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
        )

    # Both recovery operations must be attempted.
    database_session.rollback.assert_called_once()
    storage.delete.assert_called_once_with("stored-invoice.pdf")

    database_session.commit.assert_not_called()

    # The secondary failure must be recorded for investigation.
    assert "Failed to clean up uploaded document" in caplog.text
    # The cleanup failure remains observable.
    assert "Failed to clean up uploaded document" in caplog.text

    # Sensitive information must not appear in captured logs.
    assert sensitive_marker not in caplog.text
    assert "authorization=Bearer" not in caplog.text

    # Do not attach the raw SDK traceback to the log record.
    assert all(record.exc_info is None for record in caplog.records)


def test_upload_document_persists_supabase_provider() -> None:
    """Forward the selected cloud storage provider to the repository."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    storage.save.return_value = "stored-invoice.pdf"

    fake_document = MagicMock()
    fake_document.id = 25

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="stored-invoice.pdf",
        ),
        patch(
            "app.services.document_service.create_document",
            return_value=fake_document,
        ) as create_document_mock,
        patch(
            "app.services.document_service.AuditLogService",
        ),
    ):
        result = upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
            storage_provider="supabase",
        )

    assert result is fake_document

    # Verify that PostgreSQL receives the correct provider name.
    assert create_document_mock.call_args.kwargs["storage_provider"] == "supabase"

    storage.save.assert_called_once_with(
        uploaded_file.file,
        "stored-invoice.pdf",
    )

    database_session.commit.assert_called_once()
    storage.delete.assert_not_called()


def test_cloud_storage_deleted_when_audit_fails() -> None:
    """Delete the uploaded cloud object if audit logging fails."""

    database_session = MagicMock()
    storage = MagicMock()

    uploaded_file = make_upload_file(
        filename="invoice.pdf",
        content=b"Sample invoice content",
    )

    # Simulate a successful Supabase upload.
    storage.save.return_value = "cloud-invoice.pdf"

    fake_document = MagicMock()
    fake_document.id = 25

    audit_service = MagicMock()
    audit_service.record_event.side_effect = SQLAlchemyError("Audit insert failed")

    with (
        patch(
            "app.services.document_service.generate_stored_file_name",
            return_value="cloud-invoice.pdf",
        ),
        patch(
            "app.services.document_service.create_document",
            return_value=fake_document,
        ) as create_document_mock,
        patch(
            "app.services.document_service.AuditLogService",
            return_value=audit_service,
        ),
        pytest.raises(
            SQLAlchemyError,
            match="Audit insert failed",
        ),
    ):
        upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=1,
            storage=storage,
            storage_provider="supabase",
        )

    # Upload must have happened successfully.
    storage.save.assert_called_once_with(
        uploaded_file.file,
        "cloud-invoice.pdf",
    )

    # Database record was created without committing.
    create_document_mock.assert_called_once()
    assert create_document_mock.call_args.kwargs["commit"] is False

    # Audit logging was attempted without committing.
    audit_service.record_event.assert_called_once()
    assert audit_service.record_event.call_args.kwargs["commit"] is False

    # The failed operation must roll back.
    database_session.rollback.assert_called_once()
    database_session.commit.assert_not_called()

    # Remove the cloud object using its exact key.
    storage.delete.assert_called_once_with("cloud-invoice.pdf")
