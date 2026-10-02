from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.db.models.user import User
from app.repositories.document_chunk_repository import (
    search_similar_chunks,
)


def test_search_similar_chunks_returns_closest_chunk_first(
    db_session: Session,
) -> None:
    user = User(
        name="Vector Search User",
        email="vector-search@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        uploaded_by=user.id,
        original_file_name="vector-test.txt",
        stored_file_name="vector-test-stored.txt",
        file_path="uploads/vector-test-stored.txt",
        mime_type="text/plain",
        file_size=100,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="Vector search test document.",
    )

    db_session.add(document)
    db_session.flush()

    close_embedding = [1.0] + [0.0] * 1535
    medium_embedding = [0.7, 0.7] + [0.0] * 1534
    far_embedding = [0.0, 1.0] + [0.0] * 1534

    chunks = [
        DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Closest chunk",
            embedding=close_embedding,
        ),
        DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            content="Medium chunk",
            embedding=medium_embedding,
        ),
        DocumentChunk(
            document_id=document.id,
            chunk_index=2,
            content="Far chunk",
            embedding=far_embedding,
        ),
    ]

    db_session.add_all(chunks)
    db_session.commit()

    query_embedding = [1.0] + [0.0] * 1535

    results = search_similar_chunks(
        db_session,
        document_id=document.id,
        query_embedding=query_embedding,
        limit=3,
    )

    assert len(results) == 3

    assert results[0].content == "Closest chunk"
    assert results[1].content == "Medium chunk"
    assert results[2].content == "Far chunk"


def test_search_similar_chunks_only_searches_requested_document(
    db_session: Session,
) -> None:
    user = User(
        name="Isolation Test User",
        email="vector-isolation@example.com",
        password_hash="test-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    first_document = Document(
        uploaded_by=user.id,
        original_file_name="first.txt",
        stored_file_name="first-stored.txt",
        file_path="uploads/first-stored.txt",
        mime_type="text/plain",
        file_size=10,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="First document.",
    )

    second_document = Document(
        uploaded_by=user.id,
        original_file_name="second.txt",
        stored_file_name="second-stored.txt",
        file_path="uploads/second-stored.txt",
        mime_type="text/plain",
        file_size=10,
        status=DocumentStatus.TEXT_EXTRACTED,
        extracted_text="Second document.",
    )

    db_session.add_all(
        [
            first_document,
            second_document,
        ]
    )
    db_session.flush()

    matching_embedding = [1.0] + [0.0] * 1535

    first_chunk = DocumentChunk(
        document_id=first_document.id,
        chunk_index=0,
        content="Chunk from first document",
        embedding=matching_embedding,
    )

    second_chunk = DocumentChunk(
        document_id=second_document.id,
        chunk_index=0,
        content="Chunk from second document",
        embedding=matching_embedding,
    )

    db_session.add_all(
        [
            first_chunk,
            second_chunk,
        ]
    )
    db_session.commit()

    results = search_similar_chunks(
        db_session,
        document_id=first_document.id,
        query_embedding=matching_embedding,
        limit=5,
    )

    assert len(results) == 1
    assert results[0].content == "Chunk from first document"
