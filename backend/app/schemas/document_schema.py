"""
Pydantic schemas for document API responses.

These schemas define the data that DocuFlow exposes through
document-related API endpoints.
"""

from datetime import datetime

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
    created_at: datetime
    updated_at: datetime
