"""Service for retrieving document chunks relevant to a question."""

from sqlalchemy.orm import Session

from app.ai.embedder import DocumentEmbedder
from app.db.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import (
    search_similar_chunks,
)


class DocumentRetrievalService:
    """Retrieve semantically relevant chunks from an indexed document."""

    def __init__(
        self,
        embedder: DocumentEmbedder,
    ) -> None:
        self.embedder = embedder

    def retrieve(
        self,
        database_session: Session,
        *,
        document_id: int,
        question: str,
        limit: int = 5,
    ) -> list[DocumentChunk]:
        """Embed a question and retrieve the closest document chunks."""

        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        embeddings = self.embedder.embed_texts([cleaned_question])

        if len(embeddings) != 1:
            raise ValueError("Expected exactly one question embedding.")

        query_embedding = embeddings[0]

        return search_similar_chunks(
            database_session,
            document_id=document_id,
            query_embedding=query_embedding,
            limit=limit,
        )
