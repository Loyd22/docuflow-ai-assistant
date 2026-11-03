from unittest.mock import Mock

import pytest

from app.ai.exceptions import AIQuestionAnsweringError
from app.ai.qa_generator import DocumentQAGenerator


def test_generate_returns_grounded_answer() -> None:
    client = Mock()

    response = Mock()
    response.output_text = "Employees receive 15 days of annual leave per year."

    client.responses.create.return_value = response

    generator = DocumentQAGenerator(
        client=client,
    )

    answer = generator.generate(
        question="How many annual leave days do employees receive?",
        context=("Employees receive 15 days of annual leave per year."),
    )

    assert answer == ("Employees receive 15 days of annual leave per year.")

    client.responses.create.assert_called_once()


def test_generate_rejects_empty_question() -> None:
    client = Mock()

    generator = DocumentQAGenerator(
        client=client,
    )

    with pytest.raises(
        AIQuestionAnsweringError,
        match="Question cannot be empty.",
    ):
        generator.generate(
            question="   ",
            context="Some document context.",
        )

    client.responses.create.assert_not_called()


def test_generate_rejects_empty_context() -> None:
    client = Mock()

    generator = DocumentQAGenerator(
        client=client,
    )

    with pytest.raises(
        AIQuestionAnsweringError,
        match="Document context cannot be empty.",
    ):
        generator.generate(
            question="What is the policy?",
            context="   ",
        )

    client.responses.create.assert_not_called()


def test_generate_converts_provider_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Convert provider failures without exposing sensitive logs."""

    sensitive_marker = "FAKE_SECRET_DO_NOT_LOG_123"

    client = Mock()

    client.responses.create.side_effect = RuntimeError(
        f"Provider failed: authorization=Bearer {sensitive_marker}"
    )

    generator = DocumentQAGenerator(client=client)

    with pytest.raises(
        AIQuestionAnsweringError,
        match="Document question answering failed.",
    ):
        generator.generate(
            question="What is the policy?",
            context="Some document context.",
        )

    # Record the operation without exposing the exception details.
    assert "Document question answering provider call failed." in caplog.text

    assert sensitive_marker not in caplog.text
    assert "authorization=Bearer" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)

    client.responses.create.assert_called_once()
