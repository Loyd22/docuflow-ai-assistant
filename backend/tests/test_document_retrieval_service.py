from unittest.mock import Mock, patch

import pytest

from app.services.document_retrieval_service import (
    DocumentRetrievalService,
)


def test_retrieve_embeds_question_and_searches_chunks() -> None:
    embedder = Mock()

    query_embedding = [0.1] * 1536

    embedder.embed_texts.return_value = [query_embedding]

    service = DocumentRetrievalService(
        embedder=embedder,
    )

    database_session = Mock()

    expected_chunks = [
        Mock(),
        Mock(),
    ]

    with patch(
        "app.services.document_retrieval_service.search_similar_chunks",
        return_value=expected_chunks,
    ) as search_mock:
        result = service.retrieve(
            database_session,
            document_id=10,
            question="What is the leave policy?",
            limit=3,
        )

    assert result == expected_chunks

    embedder.embed_texts.assert_called_once_with(["What is the leave policy?"])

    search_mock.assert_called_once_with(
        database_session,
        document_id=10,
        query_embedding=query_embedding,
        limit=3,
    )


def test_retrieve_rejects_empty_question() -> None:
    embedder = Mock()

    service = DocumentRetrievalService(
        embedder=embedder,
    )

    database_session = Mock()

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        service.retrieve(
            database_session,
            document_id=10,
            question="   ",
        )

    embedder.embed_texts.assert_not_called()
