"""
Run the real DocuFlow invoice-extraction evaluation.

This script makes real OpenAI API requests and compares extracted
invoice fields against expected ground-truth values.
"""

from app.ai.client import create_openai_client
from app.ai.extractor import InvoiceExtractor
from evals.invoice_extraction_cases import INVOICE_EXTRACTION_CASES


def values_match(
    actual: object,
    expected: object,
) -> bool:
    """Compare evaluation values with simple numeric tolerance."""

    if actual is None or expected is None:
        return actual is expected

    if isinstance(actual, float) and isinstance(expected, float):
        return abs(actual - expected) < 0.01

    return actual == expected


def run_invoice_extraction_eval() -> None:
    """Run invoice extraction cases and report field-level accuracy."""

    client = create_openai_client()

    extractor = InvoiceExtractor(
        client=client,
    )

    total_fields = 0
    correct_fields = 0

    print("\nDocuFlow Invoice Extraction Evaluation")
    print("=" * 45)

    for case in INVOICE_EXTRACTION_CASES:
        result = extractor.extract(
            case.document_text
        )

        expected_fields = {
            "invoice_number": case.invoice_number,
            "supplier": case.supplier,
            "invoice_date": case.invoice_date,
            "due_date": case.due_date,
            "currency": case.currency,
            "subtotal": case.subtotal,
            "tax": case.tax,
            "total_amount": case.total_amount,
        }

        print(f"\nCase: {case.name}")

        for field_name, expected_value in expected_fields.items():
            actual_value = getattr(
                result,
                field_name,
            )

            is_correct = values_match(
                actual_value,
                expected_value,
            )

            total_fields += 1

            if is_correct:
                correct_fields += 1

            status = "PASS" if is_correct else "FAIL"

            print(
                f"[{status}] "
                f"{field_name}: "
                f"expected={expected_value!r}, "
                f"actual={actual_value!r}"
            )

    accuracy = (
        correct_fields / total_fields
        if total_fields
        else 0.0
    )

    print("\n" + "=" * 45)
    print(f"Correct fields: {correct_fields}/{total_fields}")
    print(f"Field accuracy: {accuracy:.2%}")


if __name__ == "__main__":
    run_invoice_extraction_eval()