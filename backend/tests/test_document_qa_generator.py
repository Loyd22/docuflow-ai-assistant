from unittest.mock import Mock

import pytest
from app.ai.qa_generator import DocumentQAGenerator

from app.ai.exceptions import AIQuestionAnsweringError


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


def test_generate_converts_provider_error() -> None:
    client = Mock()

    client.responses.create.side_effect = RuntimeError("Provider unavailable")

    generator = DocumentQAGenerator(
        client=client,
    )

    with pytest.raises(
        AIQuestionAnsweringError,
        match="Document question answering failed.",
    ):
        generator.generate(
            question="What is the policy?",
            context="Some document context.",
        )
