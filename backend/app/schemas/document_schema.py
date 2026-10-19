"""
Pydantic schemas for document API responses.

These schemas define the data that DocuFlow exposes through
document-related API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.enums import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    """Public representation of an uploaded document."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uploaded_by: int
    original_file_name: str
    mime_type: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus
    is_indexed: bool
    created_at: datetime
    updated_at: datetime


class DocumentQuestionRequest(BaseModel):
    """Question submitted about an indexed document."""

    question: str


class DocumentQuestionSource(BaseModel):
    """Retrieved document chunk supporting a generated answer."""

    chunk_index: int
    content: str


class DocumentQuestionResponse(BaseModel):
    """Grounded answer with supporting document sources."""

    answer: str
    sources: list[DocumentQuestionSource]


class DocumentIndexResponse(BaseModel):
    """Result of indexing a document for RAG retrieval."""

    document_id: int
    chunks_indexed: int


class DocumentDetailResponse(DocumentResponse):
    """Detailed document information used for review workflows."""

    extracted_text: str | None
    summary: str | None
    classification_confidence: float | None
    extracted_data: dict[str, Any] | None
    business_rule_result: dict[str, Any] | None
