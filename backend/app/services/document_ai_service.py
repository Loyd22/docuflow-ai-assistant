"""
Application service for AI document analysis.

This service orchestrates document classification and structured
field extraction while keeping provider-specific logic inside
the AI layer.
"""

from app.ai.classifier import DocumentClassifier
from app.ai.extractor import InvoiceExtractor
from app.db.enums import DocumentType
from app.schemas.ai_schema import DocumentAnalysisResult


class DocumentAIService:
    """Coordinate AI classification and structured extraction."""

    def __init__(
        self,
        classifier: DocumentClassifier,
        invoice_extractor: InvoiceExtractor,
    ) -> None:
        self.classifier = classifier
        self.invoice_extractor = invoice_extractor

    def analyze_document(
        self,
        document_text: str,
    ) -> DocumentAnalysisResult:
        """Classify a document and extract supported structured data."""

        classification = self.classifier.classify(document_text)

        extracted_data = None

        if classification.document_type == DocumentType.INVOICE:
            extracted_data = self.invoice_extractor.extract(document_text)

        return DocumentAnalysisResult(
            classification=classification,
            extracted_data=extracted_data,
        )
