"""
Evaluation examples for DocuFlow invoice extraction.

Each case contains invoice text and the expected structured fields
that should be extracted from that text.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class InvoiceExtractionCase:
    """One expected invoice-extraction example."""

    name: str
    document_text: str

    invoice_number: str | None
    supplier: str | None
    invoice_date: date | None
    due_date: date | None
    currency: str | None
    subtotal: float | None
    tax: float | None
    total_amount: float | None


INVOICE_EXTRACTION_CASES = [
    InvoiceExtractionCase(
        name="complete_invoice",
        document_text="""
        ABC Office Supplies

        INVOICE

        Invoice Number: INV-2026-001
        Invoice Date: September 18, 2026
        Due Date: September 30, 2026

        Subtotal: PHP 22,000.00
        Tax: PHP 2,640.00
        Total Amount: PHP 24,640.00
        """,
        invoice_number="INV-2026-001",
        supplier="ABC Office Supplies",
        invoice_date=date(2026, 9, 18),
        due_date=date(2026, 9, 30),
        currency="PHP",
        subtotal=22000.0,
        tax=2640.0,
        total_amount=24640.0,
    ),
    InvoiceExtractionCase(
        name="invoice_with_missing_fields",
        document_text="""
        XYZ Services

        Invoice Number: XYZ-1005
        Total Amount: USD 1,250.00
        """,
        invoice_number="XYZ-1005",
        supplier="XYZ Services",
        invoice_date=None,
        due_date=None,
        currency="USD",
        subtotal=None,
        tax=None,
        total_amount=1250.0,
    ),
    InvoiceExtractionCase(
        name="invoice_without_tax",
        document_text="""
        Tech Equipment Corporation

        INVOICE

        Invoice Number: TECH-2026-88
        Invoice Date: August 10, 2026
        Due Date: August 25, 2026

        Subtotal: PHP 80,000.00
        Total Amount: PHP 80,000.00
        """,
        invoice_number="TECH-2026-88",
        supplier="Tech Equipment Corporation",
        invoice_date=date(2026, 8, 10),
        due_date=date(2026, 8, 25),
        currency="PHP",
        subtotal=80000.0,
        tax=None,
        total_amount=80000.0,
    ),
]