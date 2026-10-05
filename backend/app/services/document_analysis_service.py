"""
Application workflow for persistent AI document analysis.

This service coordinates document state, AI analysis, business-rule
evaluation, persistence, audit logging, and workflow creation without
exposing provider-specific AI logic or deterministic business rules
to API routes.
"""

from sqlalchemy.orm import Session

from app.ai.exceptions import (
    AIClassificationError,
    AIExtractionError,
)
from app.business_rules.engine import evaluate_business_rules
from app.db.enums import (
    AuditAction,
    AuditEntityType,
    DocumentStatus,
)
from app.db.models.document import Document
from app.repositories.document_repository import (
    update_ai_analysis,
    update_business_rule_result,
    update_document_status,
)
from app.schemas.business_rule_schema import BusinessRuleResult
from app.services.audit_log_service import AuditLogService
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
        self.audit_log_service = AuditLogService(
            database_session=database_session,
        )

    def analyze(
        self,
        document: Document,
    ) -> tuple[Document, BusinessRuleResult]:
        """
        Analyze a text-extracted document, evaluate business rules,
        persist the results, and return the document and rule decision.
        """

        if document.status != DocumentStatus.TEXT_EXTRACTED:
            raise ValueError("Document is not ready for AI analysis.")

        if not document.extracted_text:
            raise ValueError("Document does not contain extracted text.")

        update_document_status(
            database_session=self.database_session,
            document=document,
            status=DocumentStatus.AI_PROCESSING,
        )

        try:
            result = self.ai_service.analyze_document(
                document.extracted_text,
            )

            business_rule_result = evaluate_business_rules(
                document_type=result.classification.document_type,
                extracted_data=result.extracted_data,
            )

            extracted_data = None

            if result.extracted_data is not None:
                extracted_data = result.extracted_data.model_dump(
                    mode="json",
                )

            update_ai_analysis(
                database_session=self.database_session,
                document=document,
                document_type=result.classification.document_type,
                classification_confidence=result.classification.confidence,
                extracted_data=extracted_data,
            )

            self.audit_log_service.record_event(
                user_id=None,
                action=AuditAction.DOCUMENT_CLASSIFIED,
                entity_type=AuditEntityType.DOCUMENT,
                entity_id=document.id,
                event_metadata={
                    "document_type": result.classification.document_type.value,
                    "confidence": result.classification.confidence,
                },
            )

            if extracted_data is not None:
                self.audit_log_service.record_event(
                    user_id=None,
                    action=AuditAction.DOCUMENT_FIELDS_EXTRACTED,
                    entity_type=AuditEntityType.DOCUMENT,
                    entity_id=document.id,
                    event_metadata={
                        "extracted_fields": sorted(
                            key
                            for key, value in extracted_data.items()
                            if value is not None
                        ),
                    },
                )

            business_rule_data = business_rule_result.model_dump(
                mode="json",
            )

            update_business_rule_result(
                database_session=self.database_session,
                document=document,
                business_rule_result=business_rule_data,
            )

            self.audit_log_service.record_event(
                user_id=None,
                action=AuditAction.RULE_CHECK_COMPLETED,
                entity_type=AuditEntityType.DOCUMENT,
                entity_id=document.id,
                event_metadata={
                    "next_action": business_rule_result.next_action.value,
                    "requires_approval": (business_rule_result.requires_approval),
                    "requires_manual_review": (
                        business_rule_result.requires_manual_review
                    ),
                },
            )

            self.workflow_service.create_from_business_rule(
                document=document,
                business_rule_result=business_rule_result,
            )

            update_document_status(
                database_session=self.database_session,
                document=document,
                status=DocumentStatus.ANALYZED,
            )

            return document, business_rule_result

        except (
            AIClassificationError,
            AIExtractionError,
        ):
            update_document_status(
                database_session=self.database_session,
                document=document,
                status=DocumentStatus.AI_PROCESSING_FAILED,
            )

            raise
