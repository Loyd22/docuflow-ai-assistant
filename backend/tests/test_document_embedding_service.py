from unittest.mock import Mock

import pytest
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


def test_embed_document_chunks_persists_embeddings(
    db_session: Session,
) -> None:
    user = User(
        name="Embedding Test User",
        email="embedding-test@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        uploaded_by=user.id,
        original_file_name="embedding-test.txt",
        stored_file_name="embedding-test-stored.txt",
        file_path="uploads/embedding-test-stored.txt",
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

    chunking_service.chunk_document(
        db_session,
        document,
    )

    stored_chunks = get_chunks_by_document_id(
        db_session,
        document.id,
    )

    embeddings = [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536,
        [0.4] * 1536,
    ]

    embedder = Mock()
    embedder.embed_texts.return_value = embeddings

    embedding_service = DocumentEmbeddingService(
        embedder=embedder,
    )

    embedded_chunks = embedding_service.embed_document_chunks(
        db_session,
        document.id,
    )

    assert len(embedded_chunks) == 4

    assert embedded_chunks[0].embedding is not None
    assert embedded_chunks[1].embedding is not None

    assert list(embedded_chunks[0].embedding) == embeddings[0]
    assert list(embedded_chunks[1].embedding) == embeddings[1]

    embedder.embed_texts.assert_called_once_with(
        [chunk.content for chunk in stored_chunks]
    )


def test_embed_document_chunks_requires_existing_chunks(
    db_session: Session,
) -> None:
    embedder = Mock()

    embedding_service = DocumentEmbeddingService(
        embedder=embedder,
    )

    with pytest.raises(
        ValueError,
        match="Document has no chunks to embed.",
    ):
        embedding_service.embed_document_chunks(
            db_session,
            document_id=999999,
        )

    embedder.embed_texts.assert_not_called()
