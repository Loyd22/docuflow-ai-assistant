from unittest.mock import Mock

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
from app.services.document_embedding_service import (
    DocumentEmbeddingService,
)
from app.services.document_indexing_service import (
    DocumentIndexingService,
)


def test_index_document_chunks_and_embeds_document(
    db_session: Session,
) -> None:
    user = User(
        name="Index Test User",
        email="index-test@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        uploaded_by=user.id,
        original_file_name="index-test.txt",
        stored_file_name="index-test-stored.txt",
        file_path="uploads/index-test-stored.txt",
        mime_type="text/plain",
        file_size=26,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="abcdefghijklmnopqrstuvwxyz",
    )

    db_session.add(document)
    db_session.flush()

    chunking_service = DocumentChunkingService(
        chunker=TextChunker(
            chunk_size=10,
            chunk_overlap=3,
        )
    )

    embedder = Mock()
    embedder.embed_texts.return_value = [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536,
        [0.4] * 1536,
    ]

    embedding_service = DocumentEmbeddingService(
        embedder=embedder,
    )

    indexing_service = DocumentIndexingService(
        chunking_service=chunking_service,
        embedding_service=embedding_service,
    )

    indexed_chunks = indexing_service.index_document(
        db_session,
        document,
    )

    stored_chunks = get_chunks_by_document_id(
        db_session,
        document.id,
    )

    assert len(indexed_chunks) == 4
    assert len(stored_chunks) == 4

    assert all(chunk.embedding is not None for chunk in stored_chunks)

    embedder.embed_texts.assert_called_once()
