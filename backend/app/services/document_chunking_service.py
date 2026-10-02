"""Service for chunking extracted document text."""

from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.rag.chunker import TextChunker
from app.repositories.document_chunk_repository import (
    create_document_chunks,
    delete_chunks_by_document_id,
)


class DocumentChunkingService:
    """Coordinates document text chunking and persistence."""

    def __init__(
        self,
        chunker: TextChunker,
    ) -> None:
        self.chunker = chunker

    def chunk_document(
        self,
        database_session: Session,
        document: Document,
    ) -> list[DocumentChunk]:
        """Split extracted text and persist the resulting chunks."""

        if not document.extracted_text:
            raise ValueError("Document must contain extracted text before chunking.")

        chunks = self.chunker.split(document.extracted_text)

        if not chunks:
            raise ValueError("Document produced no chunks.")

        delete_chunks_by_document_id(
            database_session,
            document.id,
        )

        return create_document_chunks(
            database_session,
            document_id=document.id,
            chunks=chunks,
        )
