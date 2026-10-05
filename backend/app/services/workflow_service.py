"""
Application service for document workflows and approval decisions.

This service converts deterministic business-rule decisions into
persistent workflow state and coordinates human approval decisions.
"""

from sqlalchemy.orm import Session

from app.db.enums import (
    ApprovalDecision,
    AuditAction,
    AuditEntityType,
    WorkflowStatus,
)
from app.db.models.approval import Approval
from app.db.models.document import Document
from app.db.models.workflow import Workflow
from app.repositories.approval_repository import create_approval
from app.repositories.workflow_repository import (
    create_workflow,
    get_workflow_by_document_id,
    update_workflow_status,
)
from app.schemas.business_rule_schema import (
    BusinessAction,
    BusinessRuleResult,
)
from app.services.audit_log_service import AuditLogService


class WorkflowAlreadyExistsError(Exception):
    """Raised when a document already has a workflow."""


class InvalidWorkflowStateError(Exception):
    """Raised when an action is not valid for the workflow's current state."""


class WorkflowService:
    """Coordinate document workflow creation and approval decisions."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.audit_log_service = AuditLogService(
            database_session=database_session,
        )

    def create_from_business_rule(
        self,
        document: Document,
        business_rule_result: BusinessRuleResult,
    ) -> Workflow:
        """
        Create a workflow from a deterministic business-rule result.
        """

        existing_workflow = get_workflow_by_document_id(
            database_session=self.database_session,
            document_id=document.id,
        )

        if existing_workflow is not None:
            raise WorkflowAlreadyExistsError(
                "A workflow already exists for this document."
            )

        workflow_status = self._resolve_initial_status(
            business_rule_result=business_rule_result,
        )

        workflow = create_workflow(
            database_session=self.database_session,
            document_id=document.id,
            current_status=workflow_status,
            recommended_action=business_rule_result.next_action.value,
        )

        self.audit_log_service.record_event(
            user_id=None,
            action=AuditAction.WORKFLOW_CREATED,
            entity_type=AuditEntityType.WORKFLOW,
            entity_id=workflow.id,
            event_metadata={
                "document_id": document.id,
                "initial_status": workflow.current_status.value,
                "recommended_action": business_rule_result.next_action.value,
            },
        )

        return workflow

    def record_approval_decision(
        self,
        workflow: Workflow,
        *,
        approver_id: int,
        decision: ApprovalDecision,
        comment: str | None = None,
    ) -> tuple[Workflow, Approval]:
        """
        Record a human approval decision and update the workflow state.
        """

        if workflow.current_status != WorkflowStatus.PENDING_APPROVAL:
            raise InvalidWorkflowStateError("Workflow is not waiting for approval.")

        approval = create_approval(
            database_session=self.database_session,
            workflow_id=workflow.id,
            approver_id=approver_id,
            decision=decision,
            comment=comment,
        )

        next_status = self._resolve_decision_status(
            decision=decision,
        )

        updated_workflow = update_workflow_status(
            database_session=self.database_session,
            workflow=workflow,
            status=next_status,
        )

        audit_action = self._resolve_decision_audit_action(
            decision=decision,
        )

        self.audit_log_service.record_event(
            user_id=approver_id,
            action=audit_action,
            entity_type=AuditEntityType.WORKFLOW,
            entity_id=workflow.id,
            event_metadata={
                "approval_id": approval.id,
                "previous_status": WorkflowStatus.PENDING_APPROVAL.value,
                "new_status": updated_workflow.current_status.value,
            },
        )

        return updated_workflow, approval

    @staticmethod
    def _resolve_initial_status(
        business_rule_result: BusinessRuleResult,
    ) -> WorkflowStatus:
        """
        Map a Phase 8 business action to the workflow's initial state.
        """

        if business_rule_result.next_action == BusinessAction.MANAGER_REVIEW:
            return WorkflowStatus.PENDING_APPROVAL

        if business_rule_result.next_action == BusinessAction.MANUAL_REVIEW:
            return WorkflowStatus.NEEDS_REVIEW

        if business_rule_result.next_action == BusinessAction.CONTINUE_PROCESSING:
            return WorkflowStatus.COMPLETED

        raise ValueError(
            f"Unsupported business action: {business_rule_result.next_action}"
        )

    @staticmethod
    def _resolve_decision_status(
        decision: ApprovalDecision,
    ) -> WorkflowStatus:
        """
        Map a human approval decision to its resulting workflow state.
        """

        if decision == ApprovalDecision.APPROVED:
            return WorkflowStatus.APPROVED

        if decision == ApprovalDecision.REJECTED:
            return WorkflowStatus.REJECTED

        if decision == ApprovalDecision.INFORMATION_REQUESTED:
            return WorkflowStatus.NEEDS_INFORMATION

        raise ValueError(f"Unsupported approval decision: {decision}")

    @staticmethod
    def _resolve_decision_audit_action(
        decision: ApprovalDecision,
    ) -> AuditAction:
        """
        Map a human approval decision to its audit action.
        """

        if decision == ApprovalDecision.APPROVED:
            return AuditAction.WORKFLOW_APPROVED

        if decision == ApprovalDecision.REJECTED:
            return AuditAction.WORKFLOW_REJECTED

        if decision == ApprovalDecision.INFORMATION_REQUESTED:
            return AuditAction.WORKFLOW_INFORMATION_REQUESTED

        raise ValueError(f"Unsupported approval decision: {decision}")
