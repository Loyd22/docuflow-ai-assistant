"""
Exceptions raised by DocuFlow's AI integration layer.

Provider-specific errors should be converted into application-level
exceptions before they reach services or API routes.
"""


class AIConfigurationError(Exception):
    """Raised when the AI provider is not configured correctly."""


class AIClassificationError(Exception):
    """Raised when document classification cannot be completed."""


class AIExtractionError(Exception):
    """Raised when structured document extraction cannot be completed."""
