"""
Shared database/domain enumerations.

Enums provide controlled values for important domain fields.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Roles currently supported by DocuFlow."""

    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class DocumentType(StrEnum):
    """Business document types supported by DocuFlow."""

    INVOICE = "invoice"
    CONTRACT = "contract"
    SOP = "sop"
    HR_FORM = "hr_form"
    PURCHASE_REQUEST = "purchase_request"
    POLICY = "policy"
    BUSINESS_REPORT = "business_report"
    SUPPORT_TICKET = "support_ticket"
    DIGITAL_FORM = "digital_form"
    MEMO = "memo"
    UNKNOWN = "unknown"


class DocumentStatus(StrEnum):
    """Current processing state of a document."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TEXT_EXTRACTED = "text_extracted"
    PROCESSING_FAILED = "processing_failed"

    AI_PROCESSING = "ai_processing"
    ANALYZED = "analyzed"
    AI_PROCESSING_FAILED = "ai_processing_failed"


class WorkflowStatus(StrEnum):
    """Business workflow states supported by DocuFlow."""

    NEEDS_REVIEW = "needs_review"
    NEEDS_INFORMATION = "needs_information"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class WorkflowPriority(StrEnum):
    """Priority assigned to document workflows."""

    NORMAL = "normal"
    URGENT = "urgent"


class ApprovalDecision(StrEnum):
    """Possible decisions made by an approver."""

    APPROVED = "approved"
    REJECTED = "rejected"
    INFORMATION_REQUESTED = "information_requested"


class AuditEntityType(StrEnum):
    """Entity types that can appear in audit logs."""

    USER = "user"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    APPROVAL = "approval"
    SYSTEM = "system"


class AuditAction(StrEnum):
    """Important actions tracked by DocuFlow."""

    USER_REGISTERED = "user_registered"
    USER_LOGGED_IN = "user_logged_in"

    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_TEXT_EXTRACTED = "document_text_extracted"
    DOCUMENT_CLASSIFIED = "document_classified"
    DOCUMENT_FIELDS_EXTRACTED = "document_fields_extracted"

    RULE_CHECK_COMPLETED = "rule_check_completed"

    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_INFORMATION_REQUESTED = "workflow_information_requested"
