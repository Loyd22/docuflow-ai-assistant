"""
Application workflow for persistent AI document analysis.

This service coordinates document state, AI analysis, business-rule
evaluation, and persistence without exposing provider-specific AI
logic or deterministic business rules to API routes.
"""

from sqlalchemy.orm import Session

from app.ai.exceptions import (
    AIClassificationError,
    AIExtractionError,
)
from app.business_rules.engine import evaluate_business_rules
from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.repositories.document_repository import (
    update_ai_analysis,
    update_business_rule_result,
    update_document_status,
)
from app.schemas.business_rule_schema import BusinessRuleResult
from app.services.document_ai_service import DocumentAIService
from app.services.workflow_service import WorkflowService


class DocumentAnalysisService:
    """Coordinate persistent AI analysis and business-rule evaluation."""

    def __init__(
        self,
        database_session: Session,
        ai_service: DocumentAIService,
        workflow_service: WorkflowService,
    ) -> None:
        self.database_session = database_session
        self.ai_service = ai_service
        self.workflow_service = workflow_service

    def analyze(
        self,
        document: Document,
    ) -> tuple[Document, BusinessRuleResult]:
        """
        Analyze a text-extracted document, evaluate business rules,
        persist the results, and return the document and rule decision.
        """

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
            # Phase 7:
            # Classify the document and extract supported
            # structured business data.
            result = self.ai_service.analyze_document(document.extracted_text)

            # Phase 8:
            # Apply deterministic business rules to the
            # validated AI analysis result.
            business_rule_result = evaluate_business_rules(
                document_type=result.classification.document_type,
                extracted_data=result.extracted_data,
            )

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
                classification_confidence=(result.classification.confidence),
                extracted_data=extracted_data,
            )

            # Convert the validated business-rule result into
            # JSON-compatible Python data for PostgreSQL JSONB.
            business_rule_data = business_rule_result.model_dump(mode="json")

            # Persist the deterministic Phase 8 decision.
            update_business_rule_result(
                database_session=self.database_session,
                document=document,
                business_rule_result=business_rule_data,
            )

            # Phase 9:
            # Convert the deterministic Phase 8 decision into
            # persistent workflow state.
            self.workflow_service.create_from_business_rule(
                document=document,
                business_rule_result=business_rule_result,
            )

            # The document is considered fully analyzed only
            # after both AI results and business-rule results
            # have been successfully persisted.
            update_document_status(
                database_session=self.database_session,
                document=document,
                status=DocumentStatus.ANALYZED,
            )

            # Return both:
            # 1. persistent document state
            # 2. deterministic Phase 8 business decision
            return document, business_rule_result

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
