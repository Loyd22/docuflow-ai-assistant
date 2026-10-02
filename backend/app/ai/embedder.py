"""OpenAI embedding integration for document retrieval."""

from openai import OpenAI

from app.ai.exceptions import AIEmbeddingError
from app.core.config import settings


class DocumentEmbedder:
    """Generate vector embeddings for document text."""

    def __init__(
        self,
        client: OpenAI,
    ) -> None:
        self.client = client

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple text inputs."""

        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts,
                dimensions=settings.openai_embedding_dimensions,
            )

            return [item.embedding for item in response.data]

        except Exception as error:
            raise AIEmbeddingError("Text embedding failed.") from error
