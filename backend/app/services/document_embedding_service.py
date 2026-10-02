"""Service for generating and persisting document chunk embeddings."""

from sqlalchemy.orm import Session

from app.ai.embedder import DocumentEmbedder
from app.db.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import (
    get_chunks_by_document_id,
    save_document_chunks,
)


class DocumentEmbeddingService:
    """Coordinate embedding generation and persistence for document chunks."""

    def __init__(
        self,
        embedder: DocumentEmbedder,
    ) -> None:
        self.embedder = embedder

    def embed_document_chunks(
        self,
        database_session: Session,
        document_id: int,
    ) -> list[DocumentChunk]:
        """Generate and persist embeddings for a document's chunks."""

        document_chunks = get_chunks_by_document_id(
            database_session,
            document_id,
        )

        if not document_chunks:
            raise ValueError("Document has no chunks to embed.")

        texts = [document_chunk.content for document_chunk in document_chunks]

        embeddings = self.embedder.embed_texts(texts)

        if len(embeddings) != len(document_chunks):
            raise ValueError("Embedding count does not match document chunk count.")

        for document_chunk, embedding in zip(
            document_chunks,
            embeddings,
            strict=True,
        ):
            document_chunk.embedding = embedding

        return save_document_chunks(
            database_session,
            document_chunks,
        )
