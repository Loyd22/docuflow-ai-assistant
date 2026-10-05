"""
Pydantic schemas for Phase 11 dashboard metrics.

These schemas define the summarized document and workflow
information exposed through the dashboard API.
"""

from pydantic import BaseModel


class DocumentStatusCounts(BaseModel):
    """Document totals grouped by processing status."""

    uploaded: int = 0
    processing: int = 0
    text_extracted: int = 0
    processing_failed: int = 0
    ai_processing: int = 0
    analyzed: int = 0
    ai_processing_failed: int = 0


class DocumentTypeCounts(BaseModel):
    """Document totals grouped by supported document type."""

    invoice: int = 0
    contract: int = 0
    sop: int = 0
    hr_form: int = 0
    purchase_request: int = 0
    policy: int = 0
    business_report: int = 0
    support_ticket: int = 0
    digital_form: int = 0
    memo: int = 0
    unknown: int = 0


class WorkflowStatusCounts(BaseModel):
    """Workflow totals grouped by current workflow status."""

    needs_review: int = 0
    needs_information: int = 0
    pending_approval: int = 0
    approved: int = 0
    rejected: int = 0
    completed: int = 0


class DashboardSummaryResponse(BaseModel):
    """Summary statistics displayed by the DocuFlow dashboard."""

    total_documents: int
    documents_by_status: DocumentStatusCounts
    documents_by_type: DocumentTypeCounts

    total_workflows: int
    workflows_by_status: WorkflowStatusCounts
