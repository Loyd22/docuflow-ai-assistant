"""OpenAI integration for grounded document question answering."""

import logging

from openai import OpenAI

from app.ai.exceptions import AIQuestionAnsweringError
from app.ai.prompts import DOCUMENT_QA_PROMPT
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentQAGenerator:
    """Generate answers using retrieved document context."""

    def __init__(
        self,
        client: OpenAI,
    ) -> None:
        self.client = client

    def generate(
        self,
        *,
        question: str,
        context: str,
    ) -> str:
        """Generate a grounded answer from retrieved document context."""

        cleaned_question = question.strip()
        cleaned_context = context.strip()

        if not cleaned_question:
            raise AIQuestionAnsweringError("Question cannot be empty.")

        if not cleaned_context:
            raise AIQuestionAnsweringError("Document context cannot be empty.")

        user_input = f"""
DOCUMENT CONTEXT:

{cleaned_context}

QUESTION:

{cleaned_question}
"""

        try:
            response = self.client.responses.create(
                model=settings.openai_model,
                instructions=DOCUMENT_QA_PROMPT,
                input=user_input,
            )

        except Exception as error:
            logger.exception("Document question answering provider call failed.")

            raise AIQuestionAnsweringError(
                "Document question answering failed."
            ) from error

        answer = response.output_text.strip()

        if not answer:
            raise AIQuestionAnsweringError("AI did not return a valid answer.")

        return answer
