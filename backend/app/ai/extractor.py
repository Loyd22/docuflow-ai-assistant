import logging

from openai import OpenAI

from app.ai.exceptions import AIExtractionError
from app.ai.prompts import INVOICE_EXTRACTION_PROMPT
from app.core.config import settings
from app.schemas.ai_schema import InvoiceExtraction

logger = logging.getLogger(__name__)


class InvoiceExtractor:
    """Extract structured fields from invoice text."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client

    def extract(self, document_text: str) -> InvoiceExtraction:
        """Extract validated invoice fields from document text."""

        if not document_text.strip():
            raise AIExtractionError("Invoice text cannot be empty.")

        try:
            response = self.client.responses.parse(
                model=settings.openai_model,
                instructions=INVOICE_EXTRACTION_PROMPT,
                input=document_text,
                text_format=InvoiceExtraction,
            )

        except Exception as error:
            logger.exception("Invoice extraction provider call failed.")

            raise AIExtractionError("Invoice extraction failed.") from error

        extraction = response.output_parsed

        if extraction is None:
            raise AIExtractionError("AI did not return valid invoice extraction data.")

        return extraction
