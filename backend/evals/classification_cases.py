"""
Evaluation examples for DocuFlow document classification.

These cases are intentionally small and deterministic so prompt
or model changes can be measured against the same examples.
"""

from dataclasses import dataclass

from app.db.enums import DocumentType


@dataclass(frozen=True)
class ClassificationCase:
    """One expected document-classification example."""

    name: str
    document_text: str
    expected_type: DocumentType


CLASSIFICATION_CASES = [
    ClassificationCase(
        name="basic_invoice",
        document_text="""
        ABC Office Supplies

        INVOICE

        Invoice Number: INV-2026-001
        Total Amount: PHP 24,640.00
        Due Date: September 30, 2026
        """,
        expected_type=DocumentType.INVOICE,
    ),
    ClassificationCase(
        name="basic_contract",
        document_text="""
        SERVICE AGREEMENT

        This agreement is entered into between ABC Corporation
        and XYZ Solutions.

        Effective Date: September 1, 2026

        Both parties agree to the terms and obligations described
        in this agreement.
        """,
        expected_type=DocumentType.CONTRACT,
    ),
    ClassificationCase(
        name="basic_sop",
        document_text="""
        STANDARD OPERATING PROCEDURE

        Procedure for Employee Account Creation

        Step 1: Receive the approved onboarding request.
        Step 2: Create the employee account.
        Step 3: Assign the required permissions.
        Step 4: Confirm account creation with HR.
        """,
        expected_type=DocumentType.SOP,
    ),
    ClassificationCase(
        name="basic_purchase_request",
        document_text="""
        PURCHASE REQUEST

        Requester: IT Department

        Requested Items:
        3 Laptop Computers
        3 Wireless Keyboards

        Estimated Total: PHP 150,000
        """,
        expected_type=DocumentType.PURCHASE_REQUEST,
    ),
    ClassificationCase(
        name="basic_policy",
        document_text="""
        COMPANY PASSWORD POLICY

        Employees must use passwords containing at least
        twelve characters.

        Password sharing is prohibited.

        Employees must change compromised passwords immediately.
        """,
        expected_type=DocumentType.POLICY,
    ),
    ClassificationCase(
        name="basic_memo",
        document_text="""
        MEMORANDUM

        To: All Employees
        Subject: Office Closure

        The office will be closed on September 25, 2026
        for scheduled maintenance.
        """,
        expected_type=DocumentType.MEMO,
    ),
    ClassificationCase(
        name="unknown_document",
        document_text="""
        Happy Birthday!

        Dinner starts at 7 PM.
        Please bring your favorite dessert.
        """,
        expected_type=DocumentType.UNKNOWN,
    ),
]