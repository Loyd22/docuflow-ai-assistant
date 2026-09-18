"""
Application workflow for persistent AI document analysis.

This service coordinates document state, AI analysis, and persistence
without exposing provider-specific AI logic to API routes.
"""

from sqlalchemy.orm import Session

from app.ai.exceptions import (
    AIClassificationError,
    AIExtractionError,
)
from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.repositories.document_repository import (
    update_ai_analysis,
    update_document_status,
)
from app.services.document_ai_service import DocumentAIService


class DocumentAnalysisService:
    """Coordinate persistent AI analysis for a document."""

    def __init__(
        self,
        database_session: Session,
        ai_service: DocumentAIService,
    ) -> None:
        self.database_session = database_session
        self.ai_service = ai_service

    def analyze(
        self,
        document: Document,
    ) -> Document:
        """Analyze a text-extracted document and persist the result."""

        # AI analysis should only happen after text extraction
        # has successfully completed.
        if document.status != DocumentStatus.TEXT_EXTRACTED:
            raise ValueError("Document is not ready for AI analysis.")

        # Even if the status says TEXT_EXTRACTED, make sure
        # there is actually text available for the AI.
        if not document.extracted_text:
            raise ValueError("Document does not contain extracted text.")

        # Mark the document as currently being analyzed by AI.
        update_document_status(
            database_session=self.database_session,
            document=document,
            status=DocumentStatus.AI_PROCESSING,
        )

        try:
            # DocumentAIService handles classification
            # and document-specific structured extraction.
            result = self.ai_service.analyze_document(document.extracted_text)

            extracted_data = None

            # Convert the Pydantic extraction result into
            # JSON-compatible Python data before storing it
            # in PostgreSQL's JSONB column.
            if result.extracted_data is not None:
                extracted_data = result.extracted_data.model_dump(mode="json")

            # Persist the AI-generated classification and
            # structured extraction results.
            update_ai_analysis(
                database_session=self.database_session,
                document=document,
                document_type=result.classification.document_type,
                classification_confidence=result.classification.confidence,
                extracted_data=extracted_data,
            )

            # AI analysis completed successfully.
            update_document_status(
                database_session=self.database_session,
                document=document,
                status=DocumentStatus.ANALYZED,
            )

            return document

        except (
            AIClassificationError,
            AIExtractionError,
        ):
            # If classification or extraction fails,
            # record that failure in PostgreSQL.
            update_document_status(
                database_session=self.database_session,
                document=document,
                status=DocumentStatus.AI_PROCESSING_FAILED,
            )

            # Re-raise the original AI error so the layer
            # above this service can handle it.
            raise
