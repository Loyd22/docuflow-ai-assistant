"""
Run the real DocuFlow document-classification evaluation.

This script makes real OpenAI API requests and compares model
predictions against expected document types.
"""

from app.ai.classifier import DocumentClassifier
from app.ai.client import create_openai_client
from evals.classification_cases import CLASSIFICATION_CASES


def run_classification_eval() -> None:
    """Run all classification cases and print evaluation results."""

    client = create_openai_client()

    classifier = DocumentClassifier(
        client=client,
    )

    total_cases = len(CLASSIFICATION_CASES)
    correct_cases = 0

    print("\nDocuFlow Classification Evaluation")
    print("=" * 40)

    for case in CLASSIFICATION_CASES:
        result = classifier.classify(
            case.document_text
        )

        is_correct = (
            result.document_type == case.expected_type
        )

        if is_correct:
            correct_cases += 1

        status = "PASS" if is_correct else "FAIL"

        print(f"\n[{status}] {case.name}")
        print(f"Expected:   {case.expected_type.value}")
        print(f"Predicted:  {result.document_type.value}")
        print(f"Confidence: {result.confidence:.2f}")

    accuracy = (
        correct_cases / total_cases
        if total_cases
        else 0.0
    )

    print("\n" + "=" * 40)
    print(f"Correct:  {correct_cases}/{total_cases}")
    print(f"Accuracy: {accuracy:.2%}")


if __name__ == "__main__":
    run_classification_eval()