"""Database access functions for document chunks."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.document_chunk import DocumentChunk


def create_document_chunks(
    database_session: Session,
    *,
    document_id: int,
    chunks: list[str],
) -> list[DocumentChunk]:
    """Create and persist chunks belonging to one document."""

    document_chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
        )
        for chunk_index, content in enumerate(chunks)
    ]

    database_session.add_all(document_chunks)
    database_session.commit()

    for document_chunk in document_chunks:
        database_session.refresh(document_chunk)

    return document_chunks


def get_chunks_by_document_id(
    database_session: Session,
    document_id: int,
) -> list[DocumentChunk]:
    """Return all chunks belonging to a document in original order."""

    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )

    return list(database_session.scalars(statement).all())


def delete_chunks_by_document_id(
    database_session: Session,
    document_id: int,
) -> None:
    """Delete all existing chunks belonging to a document."""

    statement = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)

    database_session.execute(statement)
    database_session.commit()


def save_document_chunks(
    database_session: Session,
    document_chunks: list[DocumentChunk],
) -> list[DocumentChunk]:
    """Persist changes made to document chunks."""

    database_session.add_all(document_chunks)
    database_session.commit()

    for document_chunk in document_chunks:
        database_session.refresh(document_chunk)

    return document_chunks


def search_similar_chunks(
    database_session: Session,
    *,
    document_id: int,
    query_embedding: list[float],
    limit: int = 5,
) -> list[DocumentChunk]:
    """Return the most semantically similar chunks for one document."""

    statement = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )

    return list(database_session.scalars(statement).all())
