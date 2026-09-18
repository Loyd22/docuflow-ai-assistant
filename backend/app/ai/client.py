"""
OpenAI client configuration.

This module owns creation of the OpenAI SDK client so provider-specific
configuration remains isolated from DocuFlow's business logic.
"""

from openai import OpenAI

from app.ai.exceptions import AIConfigurationError
from app.core.config import settings


def create_openai_client() -> OpenAI:
    """Create a configured OpenAI client."""

    if not settings.openai_api_key:
        raise AIConfigurationError("OpenAI API key is not configured.")

    return OpenAI(
        api_key=settings.openai_api_key,
    )
