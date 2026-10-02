"""Service for indexing documents for RAG retrieval."""

from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.services.document_chunking_service import DocumentChunkingService
from app.services.document_embedding_service import DocumentEmbeddingService


class DocumentIndexingService:
    """Coordinate document chunking and embedding."""

    def __init__(
        self,
        chunking_service: DocumentChunkingService,
        embedding_service: DocumentEmbeddingService,
    ) -> None:
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service

    def index_document(
        self,
        database_session: Session,
        document: Document,
    ) -> list[DocumentChunk]:
        """Chunk, embed, and persist a document for retrieval."""

        self.chunking_service.chunk_document(
            database_session,
            document,
        )

        return self.embedding_service.embed_document_chunks(
            database_session,
            document.id,
        )
