from unittest.mock import Mock

from app.services.document_qa_service import DocumentQAService


def test_answer_question_retrieves_context_and_generates_answer() -> None:
    retrieval_service = Mock()
    qa_generator = Mock()

    first_chunk = Mock()
    first_chunk.chunk_index = 0
    first_chunk.content = "Employees receive 15 days of annual leave."

    second_chunk = Mock()
    second_chunk.chunk_index = 1
    second_chunk.content = "Unused leave may be carried forward."

    retrieval_service.retrieve.return_value = [
        first_chunk,
        second_chunk,
    ]

    qa_generator.generate.return_value = "Employees receive 15 days of annual leave."

    service = DocumentQAService(
        retrieval_service=retrieval_service,
        qa_generator=qa_generator,
    )

    database_session = Mock()

    result = service.answer_question(
        database_session,
        document_id=10,
        question="How many annual leave days do employees receive?",
        limit=5,
    )

    assert result.answer == ("Employees receive 15 days of annual leave.")

    assert len(result.sources) == 2

    assert result.sources[0].chunk_index == 0
    assert result.sources[0].content == ("Employees receive 15 days of annual leave.")

    assert result.sources[1].chunk_index == 1
    assert result.sources[1].content == ("Unused leave may be carried forward.")

    retrieval_service.retrieve.assert_called_once_with(
        database_session,
        document_id=10,
        question="How many annual leave days do employees receive?",
        limit=5,
    )

    qa_generator.generate.assert_called_once_with(
        question="How many annual leave days do employees receive?",
        context=(
            "Employees receive 15 days of annual leave.\n\n"
            "Unused leave may be carried forward."
        ),
    )


def test_answer_question_returns_fallback_when_no_chunks_found() -> None:
    retrieval_service = Mock()
    qa_generator = Mock()

    retrieval_service.retrieve.return_value = []

    service = DocumentQAService(
        retrieval_service=retrieval_service,
        qa_generator=qa_generator,
    )

    database_session = Mock()

    result = service.answer_question(
        database_session,
        document_id=10,
        question="What is the maternity leave policy?",
    )

    assert result.answer == (
        "I could not find enough information in the document to answer that question."
    )

    assert result.sources == []

    qa_generator.generate.assert_not_called()
