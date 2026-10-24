"""
Application service for document workflows and approval decisions.

This service converts deterministic business-rule decisions into
persistent workflow state and coordinates human approval decisions.
"""

from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.business_rules.engine import evaluate_business_rules
from app.db.enums import (
    ApprovalDecision,
    AuditAction,
    AuditEntityType,
    DocumentType,
    ReviewOutcome,
    WorkflowStatus,
)
from app.db.models.approval import Approval
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow
from app.db.models.workflow_information_request import WorkflowInformationRequest
from app.db.models.workflow_review import WorkflowReview
from app.repositories.approval_repository import create_approval
from app.repositories.workflow_information_request_repository import (
    create_information_request,
    get_open_information_request,
    record_information_response,
)
from app.repositories.workflow_repository import (
    create_workflow,
    get_workflow_by_document_id,
    get_workflow_for_update,
    update_workflow_status,
)
from app.repositories.workflow_review_repository import create_workflow_review
from app.schemas.ai_schema import InvoiceExtraction
from app.schemas.business_rule_schema import (
    BusinessAction,
    BusinessRuleResult,
)
from app.security.document_access_policy import DocumentAccessPolicy
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
        """Save an approval decision and related changes together."""

        try:
            # Lock the workflow before checking its current status.
            locked_workflow = get_workflow_for_update(
                database_session=self.database_session,
                workflow_id=workflow.id,
            )

            if locked_workflow is None:
                raise InvalidWorkflowStateError("Workflow no longer exists.")

            workflow = locked_workflow

            # Load the user who is submitting the decision.
            approver = self.database_session.get(User, approver_id)

            # Check permissions against the locked workflow.
            if approver is None or not DocumentAccessPolicy.can_make_workflow_decision(
                workflow=workflow,
                current_user=approver,
            ):
                raise PermissionError(
                    "You are not allowed to make a decision on this workflow."
                )

            # Only workflows awaiting approval can receive a decision.
            if workflow.current_status != WorkflowStatus.PENDING_APPROVAL:
                raise InvalidWorkflowStateError("Workflow is not waiting for approval.")

            # Remove surrounding spaces from the manager's comment.
            clean_comment = comment.strip() if comment else None

            # Rejection and information requests require an explanation.
            if (
                decision
                in (
                    ApprovalDecision.REJECTED,
                    ApprovalDecision.INFORMATION_REQUESTED,
                )
                and not clean_comment
            ):
                raise ValueError(
                    "A comment is required when rejecting a document "
                    "or requesting information."
                )

            next_status = self._resolve_decision_status(
                decision=decision,
            )

            # Save the decision without committing yet.
            approval = create_approval(
                database_session=self.database_session,
                workflow_id=workflow.id,
                approver_id=approver_id,
                decision=decision,
                comment=clean_comment,
                commit=False,
            )

            # Create a request for the document's employee.
            if decision == ApprovalDecision.INFORMATION_REQUESTED:
                create_information_request(
                    database_session=self.database_session,
                    workflow_id=workflow.id,
                    requested_by=approver_id,
                    request_comment=clean_comment,
                    return_status=WorkflowStatus.PENDING_APPROVAL.value,
                    approval_id=approval.id,
                )

            updated_workflow = update_workflow_status(
                database_session=self.database_session,
                workflow=workflow,
                status=next_status,
                commit=False,
            )

            audit_action = self._resolve_decision_audit_action(
                decision=decision,
            )

            # Record the decision in the same transaction.
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
                commit=False,
            )

            # Commit the decision, request, status and audit log together.
            self.database_session.commit()
            self.database_session.refresh(updated_workflow)
            self.database_session.refresh(approval)

            return updated_workflow, approval

        except Exception:
            # Undo every change if any operation fails.
            self.database_session.rollback()
            raise

    def record_manual_review(
        self,
        workflow: Workflow,
        *,
        reviewer_id: int,
        outcome: ReviewOutcome,
        comment: str,
        corrected_total_amount: float | None = None,
    ) -> tuple[Workflow, WorkflowReview]:
        """Record a manual review and recheck invoice rules when resolved."""

        # Lock the latest workflow before checking its status.
        locked_workflow = get_workflow_for_update(
            database_session=self.database_session,
            workflow_id=workflow.id,
        )

        if locked_workflow is None:
            raise InvalidWorkflowStateError("Workflow no longer exists.")

        # Use the latest workflow from the database.
        workflow = locked_workflow

        # Load the manager or admin submitting the review.
        reviewer = self.database_session.get(
            User,
            reviewer_id,
        )

        # Check permissions using the latest workflow assignment.
        if reviewer is None or not DocumentAccessPolicy.can_make_workflow_decision(
            workflow=workflow,
            current_user=reviewer,
        ):
            raise PermissionError("You are not allowed to review this workflow.")

        # Prevent duplicate reviews of completed or rejected workflows.
        if workflow.current_status != WorkflowStatus.NEEDS_REVIEW:
            raise InvalidWorkflowStateError(
                "Workflow is not waiting for manual review."
            )

        # Require a meaningful review comment.
        comment = comment.strip()

        if not comment:
            raise ValueError("A review comment is required.")

        # Only resolved reviews may include a corrected amount.
        if outcome != ReviewOutcome.RESOLVED and corrected_total_amount is not None:
            raise ValueError(
                "A corrected total is allowed only when resolving a review."
            )

        document = workflow.document

        if document is None:
            raise ValueError("Workflow document was not found.")

        new_extracted_data = None
        new_rule_result = None

        if outcome == ReviewOutcome.RESOLVED:
            # Automatic resolution currently supports invoices only.
            if document.document_type != DocumentType.INVOICE:
                raise ValueError(
                    "Automatic resolution is currently supported only for invoices."
                )

            if corrected_total_amount is None:
                raise ValueError("A corrected invoice total is required.")

            try:
                amount = Decimal(str(corrected_total_amount))
            except InvalidOperation as exc:
                raise ValueError("Invalid invoice total.") from exc

            if not amount.is_finite() or amount < 0:
                raise ValueError("Invoice total must be a finite, nonnegative number.")

            # Preserve the remaining AI-extracted fields.
            new_extracted_data = dict(document.extracted_data or {})
            new_extracted_data["total_amount"] = float(amount)

            try:
                invoice = InvoiceExtraction.model_validate(new_extracted_data)
            except ValidationError as exc:
                raise ValueError("Corrected invoice data is invalid.") from exc

            # Reevaluate the corrected invoice using business rules.
            new_rule_result = evaluate_business_rules(
                document_type=document.document_type,
                extracted_data=invoice,
            )

            if new_rule_result.requires_manual_review:
                raise ValueError("Invoice still requires manual review.")

            # Determine the next workflow status.
            if new_rule_result.next_action == BusinessAction.MANAGER_REVIEW:
                next_status = WorkflowStatus.PENDING_APPROVAL

            elif new_rule_result.next_action == BusinessAction.CONTINUE_PROCESSING:
                next_status = WorkflowStatus.COMPLETED

            else:
                raise ValueError("Unsupported business-rule action.")

            audit_action = AuditAction.WORKFLOW_REVIEW_RESOLVED

        elif outcome == ReviewOutcome.REJECTED:
            next_status = WorkflowStatus.REJECTED
            audit_action = AuditAction.WORKFLOW_REVIEW_REJECTED

        elif outcome == ReviewOutcome.INFORMATION_REQUESTED:
            next_status = WorkflowStatus.NEEDS_INFORMATION
            audit_action = AuditAction.WORKFLOW_REVIEW_INFORMATION_REQUESTED

        else:
            raise ValueError("Unsupported manual-review outcome.")

        previous_status = workflow.current_status
        previous_total = None

        if new_extracted_data is not None:
            previous_total = (document.extracted_data or {}).get("total_amount")

        try:
            # Stage corrected data and business-rule results.
            if new_extracted_data is not None and new_rule_result is not None:
                document.extracted_data = new_extracted_data
                document.business_rule_result = new_rule_result.model_dump(mode="json")
                self.database_session.add(document)

            # Move the workflow to its next status.
            workflow.current_status = next_status
            self.database_session.add(workflow)

            # Save the manager's review decision.
            review = create_workflow_review(
                database_session=self.database_session,
                workflow_id=workflow.id,
                reviewer_id=reviewer_id,
                outcome=outcome,
                comment=comment,
            )

            # Create a request if more information is needed.
            if outcome == ReviewOutcome.INFORMATION_REQUESTED:
                create_information_request(
                    database_session=self.database_session,
                    workflow_id=workflow.id,
                    requested_by=reviewer_id,
                    request_comment=comment,
                    return_status=WorkflowStatus.NEEDS_REVIEW.value,
                    review_id=review.id,
                )

            # Record the decision and correction history.
            self.audit_log_service.record_event(
                user_id=reviewer_id,
                action=audit_action,
                entity_type=AuditEntityType.WORKFLOW,
                entity_id=workflow.id,
                event_metadata={
                    "review_id": review.id,
                    "previous_status": previous_status.value,
                    "new_status": next_status.value,
                    "previous_total_amount": previous_total,
                    "corrected_total_amount": (
                        new_extracted_data["total_amount"]
                        if new_extracted_data is not None
                        else None
                    ),
                    "business_rule_result": (
                        new_rule_result.model_dump(mode="json")
                        if new_rule_result is not None
                        else None
                    ),
                },
                commit=False,
            )

            # Commit the review and audit log together.
            self.database_session.commit()
            self.database_session.refresh(workflow)
            self.database_session.refresh(review)

            return workflow, review

        except Exception:
            # Undo staged database changes when saving fails.
            self.database_session.rollback()
            raise

    def respond_to_information_request(
        self,
        workflow: Workflow,
        *,
        employee_id: int,
        response_comment: str,
    ) -> tuple[Workflow, WorkflowInformationRequest]:
        """Save an employee response and return the workflow to review."""

        try:
            # Lock the workflow to prevent conflicting updates.
            locked_workflow = get_workflow_for_update(
                database_session=self.database_session,
                workflow_id=workflow.id,
            )

            if locked_workflow is None:
                raise InvalidWorkflowStateError("Workflow no longer exists.")

            workflow = locked_workflow
            document = workflow.document

            # Only the document owner can answer the request.
            if document is None:
                raise InvalidWorkflowStateError("Workflow document was not found.")

            if document.uploaded_by != employee_id:
                raise PermissionError(
                    "You cannot respond to another employee's request."
                )

            # The workflow must be waiting for information.
            if workflow.current_status != WorkflowStatus.NEEDS_INFORMATION:
                raise InvalidWorkflowStateError(
                    "Workflow is not waiting for information."
                )

            clean_response = response_comment.strip()
            if not clean_response:
                raise ValueError("An information response is required.")

            # Retrieve the unanswered information request.
            information_request = get_open_information_request(
                database_session=self.database_session,
                workflow_id=workflow.id,
                for_update=True,
            )

            if information_request is None:
                raise InvalidWorkflowStateError(
                    "No unanswered information request was found."
                )

            # Return to the review queue that asked for the information.
            next_status = WorkflowStatus(information_request.return_status)
            if next_status not in (
                WorkflowStatus.NEEDS_REVIEW,
                WorkflowStatus.PENDING_APPROVAL,
            ):
                raise InvalidWorkflowStateError(
                    "Invalid information request return status."
                )

            information_request = record_information_response(
                database_session=self.database_session,
                information_request=information_request,
                responded_by=employee_id,
                response_comment=clean_response,
            )

            workflow.current_status = next_status
            self.database_session.add(workflow)

            # Keep the response and status change in the audit trail.
            self.audit_log_service.record_event(
                user_id=employee_id,
                action=AuditAction.WORKFLOW_INFORMATION_RESPONDED,
                entity_type=AuditEntityType.WORKFLOW,
                entity_id=workflow.id,
                event_metadata={
                    "information_request_id": information_request.id,
                    "previous_status": WorkflowStatus.NEEDS_INFORMATION.value,
                    "new_status": next_status.value,
                    "responded_by": employee_id,
                },
                commit=False,
            )

            # Commit response, workflow, and audit log together.
            self.database_session.commit()
            self.database_session.refresh(workflow)
            self.database_session.refresh(information_request)
            return workflow, information_request

        except Exception:
            self.database_session.rollback()
            raise

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
