"""Shared permission rules for documents and workflows."""

from app.db.enums import UserRole, WorkflowStatus
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow


class DocumentAccessPolicy:
    """Determine who can read documents and manage workflows."""

    REVIEW_QUEUE_STATUSES = frozenset(
        {
            WorkflowStatus.NEEDS_REVIEW,
            WorkflowStatus.PENDING_APPROVAL,
            WorkflowStatus.NEEDS_INFORMATION,
        }
    )

    @staticmethod
    def can_read_document(
        *,
        document: Document,
        current_user: User,
    ) -> bool:
        """Check whether a user may read a document."""

        # Admins can read all documents.
        if current_user.role == UserRole.ADMIN:
            return True

        # Users can read their own uploaded documents.
        if document.uploaded_by == current_user.id:
            return True

        # Managers may read documents in their review scope.
        if current_user.role == UserRole.MANAGER:
            workflow = document.workflow

            if workflow is None:
                return False

            # A manager can read an assigned workflow's document.
            if workflow.assigned_to == current_user.id:
                return True

            # Unassigned review work belongs to the shared queue.
            if workflow.assigned_to is None:
                return (
                    workflow.current_status
                    in DocumentAccessPolicy.REVIEW_QUEUE_STATUSES
                )

        return False

    @staticmethod
    def can_make_workflow_decision(
        *,
        workflow: Workflow,
        current_user: User,
    ) -> bool:
        """Check whether a manager or admin may act on a workflow."""

        # Admins can manage workflows regardless of assignment.
        if current_user.role == UserRole.ADMIN:
            return True

        if current_user.role != UserRole.MANAGER:
            return False

        # Managers can act only on unassigned or assigned work.
        return workflow.assigned_to in (
            None,
            current_user.id,
        )

    @staticmethod
    def can_view_workflow(
        *,
        workflow: Workflow,
        current_user: User,
    ) -> bool:
        """Check whether a user can see a workflow."""

        # Admins can see every workflow.
        if current_user.role == UserRole.ADMIN:
            return True

        # The workflow must have an associated document.
        document = workflow.document
        if document is None:
            return False

        # Employees can see workflows for their own documents.
        if current_user.role == UserRole.EMPLOYEE:
            return document.uploaded_by == current_user.id

        # Managers can see assigned or eligible shared workflows.
        if current_user.role == UserRole.MANAGER:
            if workflow.assigned_to == current_user.id:
                return True

            if workflow.assigned_to is None:
                return (
                    workflow.current_status
                    in DocumentAccessPolicy.REVIEW_QUEUE_STATUSES
                )

        return False
