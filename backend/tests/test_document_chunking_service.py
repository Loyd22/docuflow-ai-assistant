from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.db.models.user import User
from app.rag.chunker import TextChunker
from app.repositories.document_chunk_repository import (
    get_chunks_by_document_id,
)
from app.services.document_chunking_service import (
    DocumentChunkingService,
)


def test_chunk_document_persists_chunks(
    db_session: Session,
) -> None:
    user = User(
        name="Test User",
        email="chunk-test@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        uploaded_by=user.id,
        original_file_name="test.txt",
        stored_file_name="test-stored.txt",
        file_path="uploads/test-stored.txt",
        mime_type="text/plain",
        file_size=26,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="abcdefghijklmnopqrstuvwxyz",
    )

    db_session.add(document)
    db_session.flush()

    service = DocumentChunkingService(
        chunker=TextChunker(
            chunk_size=10,
            chunk_overlap=3,
        )
    )

    chunks = service.chunk_document(
        db_session,
        document,
    )

    stored_chunks = get_chunks_by_document_id(
        db_session,
        document.id,
    )

    assert len(chunks) == 4
    assert len(stored_chunks) == 4

    assert stored_chunks[0].chunk_index == 0
    assert stored_chunks[0].content == "abcdefghij"
    assert stored_chunks[0].embedding is None

    assert stored_chunks[1].chunk_index == 1
    assert stored_chunks[1].content == "hijklmnopq"


def test_rechunk_document_replaces_existing_chunks(
    db_session: Session,
) -> None:
    user = User(
        name="Rechunk Test User",
        email="rechunk-test@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        uploaded_by=user.id,
        original_file_name="rechunk.txt",
        stored_file_name="rechunk-stored.txt",
        file_path="uploads/rechunk-stored.txt",
        mime_type="text/plain",
        file_size=26,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="abcdefghijklmnopqrstuvwxyz",
    )

    db_session.add(document)
    db_session.flush()

    service = DocumentChunkingService(
        chunker=TextChunker(
            chunk_size=10,
            chunk_overlap=3,
        )
    )

    first_chunks = service.chunk_document(
        db_session,
        document,
    )

    assert len(first_chunks) == 4

    document.extracted_text = "1234567890ABCDEFGHIJ"

    second_chunks = service.chunk_document(
        db_session,
        document,
    )

    stored_chunks = get_chunks_by_document_id(
        db_session,
        document.id,
    )

    assert len(second_chunks) == 3
    assert len(stored_chunks) == 3

    assert stored_chunks[0].chunk_index == 0
    assert stored_chunks[0].content == "1234567890"

    assert stored_chunks[1].chunk_index == 1
    assert stored_chunks[1].content == "890ABCDEFG"

    assert stored_chunks[2].chunk_index == 2
    assert stored_chunks[2].content == "EFGHIJ"
