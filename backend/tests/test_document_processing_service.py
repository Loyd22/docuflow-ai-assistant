"""
Tests for document processing service behavior.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.db.enums import DocumentStatus
from app.processing.exceptions import DocumentProcessingError
from app.services.document_processing_service import process_document


class FakeDocument:
    """Minimal document object required by the processing service."""

    def __init__(
        self,
        file_path: str,
        document_id: int = 1,
        stored_file_name: str | None = None,
    ) -> None:
        self.id = document_id
        self.file_path = file_path
        self.stored_file_name = stored_file_name or Path(file_path).name
        self.extracted_text = None
        self.status = DocumentStatus.UPLOADED


def test_process_document_marks_document_as_text_extracted(
    tmp_path: Path,
) -> None:
    """Successful processing should mark the document as text extracted."""

    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "DocuFlow processing test.",
        encoding="utf-8",
    )

    document = FakeDocument(str(file_path))
    database_session = Mock()

    with patch(
        "app.services.document_processing_service.save_document",
        side_effect=lambda session, doc: doc,
    ):
        result = process_document(
            database_session,
            document,
        )

    assert result.status == DocumentStatus.TEXT_EXTRACTED


def test_process_document_marks_document_as_processing_failed(
    tmp_path: Path,
) -> None:
    """Failed extraction should mark the document as processing failed."""

    missing_file = tmp_path / "missing.txt"

    document = FakeDocument(str(missing_file))
    database_session = Mock()

    with (
        patch(
            "app.services.document_processing_service.save_document",
            side_effect=lambda session, doc: doc,
        ),
        pytest.raises(
            DocumentProcessingError,
            match="Document processing failed",
        ),
    ):
        process_document(
            database_session,
            document,
        )

    assert document.status == DocumentStatus.PROCESSING_FAILED


def test_process_document_with_injected_storage(
    tmp_path: Path,
) -> None:
    """Extract text from a file retrieved through storage."""

    document = FakeDocument(
        file_path="cloud-file-reference",
        stored_file_name="stored-invoice.txt",
    )

    database_session = Mock()
    storage = Mock()

    downloaded_paths = []

    def fake_download(storage_key: str, destination: Path) -> None:
        assert storage_key == "stored-invoice.txt"

        downloaded_paths.append(destination)
        destination.write_text(
            "Cloud document content",
            encoding="utf-8",
        )

    storage.download_to_path.side_effect = fake_download

    with patch(
        "app.services.document_processing_service.save_document",
        side_effect=lambda session, doc: doc,
    ):
        result = process_document(
            database_session,
            document,
            storage=storage,
        )

    assert result.extracted_text == "Cloud document content"
    assert result.status == DocumentStatus.TEXT_EXTRACTED

    assert len(downloaded_paths) == 1
    assert downloaded_paths[0].suffix == ".txt"

    # The temporary document must be deleted.
    assert not downloaded_paths[0].exists()


def test_process_document_cleans_up_when_extraction_fails() -> None:
    """Temporary files must be deleted after extraction errors."""

    document = FakeDocument(
        file_path="cloud-file-reference",
        stored_file_name="stored-invoice.txt",
    )

    database_session = Mock()
    storage = Mock()

    downloaded_paths = []

    def fake_download(storage_key: str, destination: Path) -> None:
        downloaded_paths.append(destination)
        destination.write_text(
            "Document content",
            encoding="utf-8",
        )

    storage.download_to_path.side_effect = fake_download

    with (
        patch(
            "app.services.document_processing_service.save_document",
            side_effect=lambda session, doc: doc,
        ),
        patch(
            "app.services.document_processing_service.extract_document_text",
            side_effect=DocumentProcessingError("Extraction failed"),
        ),
        pytest.raises(
            DocumentProcessingError,
            match="Extraction failed",
        ),
    ):
        process_document(
            database_session,
            document,
            storage=storage,
        )

    assert document.status == DocumentStatus.PROCESSING_FAILED
    assert len(downloaded_paths) == 1
    assert not downloaded_paths[0].exists()


def test_process_document_handles_storage_download_failure() -> None:
    """A download failure must update document processing status."""

    document = FakeDocument(
        file_path="cloud-file-reference",
        stored_file_name="stored-invoice.txt",
    )

    database_session = Mock()
    storage = Mock()

    storage.download_to_path.side_effect = OSError("Storage unavailable")

    with (
        patch(
            "app.services.document_processing_service.save_document",
            side_effect=lambda session, doc: doc,
        ),
        pytest.raises(
            DocumentProcessingError,
            match="Document processing failed",
        ),
    ):
        process_document(
            database_session,
            document,
            storage=storage,
        )

    assert document.status == DocumentStatus.PROCESSING_FAILED


def test_process_document_extracts_and_saves_text(
    tmp_path: Path,
) -> None:
    """Processing should extract text and persist the document."""

    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "DocuFlow processing test.",
        encoding="utf-8",
    )

    document = FakeDocument(str(file_path))
    database_session = Mock()

    with patch(
        "app.services.document_processing_service.save_document",
        side_effect=lambda session, doc: doc,
    ) as mocked_save_document:
        result = process_document(
            database_session,
            document,
        )

    assert result.extracted_text == "DocuFlow processing test."
    assert result.status == DocumentStatus.TEXT_EXTRACTED

    # Verify that the updated document was persisted.
    mocked_save_document.assert_called_with(
        database_session,
        document,
    )
