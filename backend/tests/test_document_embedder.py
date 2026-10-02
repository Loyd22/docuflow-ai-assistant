from unittest.mock import Mock

import pytest

from app.ai.embedder import DocumentEmbedder
from app.ai.exceptions import AIEmbeddingError


def test_embed_texts_returns_embeddings() -> None:
    client = Mock()

    first_embedding = [0.1] * 1536
    second_embedding = [0.2] * 1536

    first_item = Mock()
    first_item.embedding = first_embedding

    second_item = Mock()
    second_item.embedding = second_embedding

    response = Mock()
    response.data = [
        first_item,
        second_item,
    ]

    client.embeddings.create.return_value = response

    embedder = DocumentEmbedder(
        client=client,
    )

    embeddings = embedder.embed_texts(
        [
            "First document chunk.",
            "Second document chunk.",
        ]
    )

    assert len(embeddings) == 2
    assert embeddings[0] == first_embedding
    assert embeddings[1] == second_embedding


def test_embed_texts_returns_empty_list_for_empty_input() -> None:
    client = Mock()

    embedder = DocumentEmbedder(
        client=client,
    )

    embeddings = embedder.embed_texts([])

    assert embeddings == []

    client.embeddings.create.assert_not_called()


def test_embed_texts_converts_provider_error() -> None:
    client = Mock()

    client.embeddings.create.side_effect = RuntimeError("Provider unavailable")

    embedder = DocumentEmbedder(
        client=client,
    )

    with pytest.raises(
        AIEmbeddingError,
        match="Text embedding failed.",
    ):
        embedder.embed_texts(["Some document text."])
