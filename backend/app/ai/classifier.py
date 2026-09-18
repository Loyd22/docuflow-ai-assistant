import logging

from openai import OpenAI

from app.ai.exceptions import AIClassificationError
from app.ai.prompts import DOCUMENT_CLASSIFICATION_PROMPT
from app.core.config import settings
from app.schemas.ai_schema import DocumentClassification

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classify extracted document text using an AI model."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client

    def classify(self, document_text: str) -> DocumentClassification:
        """Classify document text into a supported DocuFlow document type."""

        if not document_text.strip():
            raise AIClassificationError("Document text cannot be empty.")

        try:
            response = self.client.responses.parse(
                model=settings.openai_model,
                instructions=DOCUMENT_CLASSIFICATION_PROMPT,
                input=document_text,
                text_format=DocumentClassification,
            )

        except Exception as error:
            logger.exception("Document classification provider call failed.")

            raise AIClassificationError("Document classification failed.") from error

        classification = response.output_parsed

        if classification is None:
            raise AIClassificationError(
                "AI did not return a valid document classification."
            )

        return classification
