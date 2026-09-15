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

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.extracted_text = None
        self.status = DocumentStatus.UPLOADED


def test_process_document_extracts_and_saves_text(
    tmp_path: Path,
) -> None:
    """Processing should extract text and persist the changed document."""

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

    mocked_save_document.assert_called_with(
        database_session,
        document,
    )


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
