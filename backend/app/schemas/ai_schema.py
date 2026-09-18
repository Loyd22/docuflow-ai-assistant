"""
Pydantic schemas for AI document analysis.

These schemas define the structured contracts that AI-generated
classification and extraction results must satisfy before the
application trusts or persists them.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.db.enums import DocumentType


class DocumentClassification(BaseModel):
    """Validated classification result for a processed document."""

    document_type: DocumentType
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class InvoiceExtraction(BaseModel):
    """Structured business data extracted from an invoice."""

    invoice_number: str | None = None
    supplier: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    currency: str | None = None

    subtotal: float | None = Field(
        default=None,
        ge=0,
    )

    tax: float | None = Field(
        default=None,
        ge=0,
    )

    total_amount: float | None = Field(
        default=None,
        ge=0,
    )


class DocumentAnalysisResult(BaseModel):
    """Combined result of AI document classification and extraction."""

    classification: DocumentClassification
    extracted_data: InvoiceExtraction | None = None
