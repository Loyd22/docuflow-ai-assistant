"""Run the real DocuFlow RAG evaluation.

This script indexes one deterministic evaluation document,
asks predefined questions using the real RAG pipeline, and
checks both answer content and retrieved source content.
"""

from app.ai.client import create_openai_client
from app.ai.embedder import DocumentEmbedder
from app.ai.qa_generator import DocumentQAGenerator
from app.db.enums import DocumentStatus
from app.db.session import SessionLocal
from app.rag.chunker import TextChunker
from app.repositories.document_repository import (
    create_document,
    save_document,
)
from app.repositories.user_repository import UserRepository
from app.services.document_chunking_service import (
    DocumentChunkingService,
)
from app.services.document_embedding_service import (
    DocumentEmbeddingService,
)
from app.services.document_indexing_service import (
    DocumentIndexingService,
)
from app.services.document_qa_service import DocumentQAService
from app.services.document_retrieval_service import (
    DocumentRetrievalService,
)
from evals.rag_cases import RAG_CASES, RAG_DOCUMENT_TEXT

EVAL_USER_EMAIL = "rag-eval@docuflow.local"


def contains_all_terms(
    text: str,
    expected_terms: tuple[str, ...],
) -> bool:
    """Return True when all expected terms appear in the text."""

    normalized_text = text.lower()

    return all(term.lower() in normalized_text for term in expected_terms)


def contains_any_term(
    text: str,
    expected_terms: tuple[str, ...],
) -> bool:
    """Return True when at least one expected term appears in the text."""

    if not expected_terms:
        return True

    normalized_text = text.lower()

    return any(term.lower() in normalized_text for term in expected_terms)


def run_rag_eval() -> None:
    """Run all RAG evaluation cases and print results."""

    database_session = SessionLocal()

    document = None

    try:
        user_repository = UserRepository(
            database_session,
        )

        user = user_repository.get_by_email(
            EVAL_USER_EMAIL,
        )

        if user is None:
            user = user_repository.create(
                name="RAG Evaluation User",
                email=EVAL_USER_EMAIL,
                password_hash="evaluation-only",
            )

        document = create_document(
            database_session,
            uploaded_by=user.id,
            original_file_name="rag-evaluation.txt",
            stored_file_name="rag-evaluation.txt",
            file_path="evals/rag-evaluation.txt",
            mime_type="text/plain",
            file_size=len(RAG_DOCUMENT_TEXT.encode("utf-8")),
            status=DocumentStatus.TEXT_EXTRACTED,
        )

        document.extracted_text = RAG_DOCUMENT_TEXT

        save_document(
            database_session,
            document,
        )

        client = create_openai_client()

        chunker = TextChunker(
            chunk_size=400,
            chunk_overlap=80,
        )

        chunking_service = DocumentChunkingService(
            chunker=chunker,
        )

        embedder = DocumentEmbedder(
            client=client,
        )

        embedding_service = DocumentEmbeddingService(
            embedder=embedder,
        )

        indexing_service = DocumentIndexingService(
            chunking_service=chunking_service,
            embedding_service=embedding_service,
        )

        retrieval_service = DocumentRetrievalService(
            embedder=embedder,
        )

        qa_generator = DocumentQAGenerator(
            client=client,
        )

        qa_service = DocumentQAService(
            retrieval_service=retrieval_service,
            qa_generator=qa_generator,
        )

        indexed_chunks = indexing_service.index_document(
            database_session,
            document,
        )

        total_cases = len(RAG_CASES)
        passed_cases = 0
        retrieval_passes = 0
        answer_passes = 0

        print("\nDocuFlow RAG Evaluation")
        print("=" * 50)
        print(f"Indexed chunks: {len(indexed_chunks)}")

        for case in RAG_CASES:
            result = qa_service.answer_question(
                database_session,
                document_id=document.id,
                question=case.question,
            )

            top_source_text = result.sources[0].content if result.sources else ""

            answer_required_terms_correct = contains_all_terms(
                result.answer,
                case.expected_answer_terms,
            )

            answer_alternative_terms_correct = contains_any_term(
                result.answer,
                case.expected_answer_any_terms,
            )

            answer_correct = (
                answer_required_terms_correct and answer_alternative_terms_correct
            )

            retrieval_correct = contains_all_terms(
                top_source_text,
                case.expected_source_terms,
            )

            if answer_correct:
                answer_passes += 1

            if retrieval_correct:
                retrieval_passes += 1

            case_passed = answer_correct and retrieval_correct

            if case_passed:
                passed_cases += 1

            status = "PASS" if case_passed else "FAIL"

            print(f"\n[{status}] {case.name}")
            print(f"Question: {case.question}")
            print(f"Answer:   {result.answer}")
            print(f"Retrieval: {'PASS' if retrieval_correct else 'FAIL'}")
            print(f"Answer:    {'PASS' if answer_correct else 'FAIL'}")

            print("Expected answer terms:")
            for term in case.expected_answer_terms:
                print(f"  - {term}")

            if case.expected_answer_any_terms:
                print("Expected answer alternatives:")
                for term in case.expected_answer_any_terms:
                    print(f"  - {term}")

            print("Expected source terms:")
            for term in case.expected_source_terms:
                print(f"  - {term}")

            print("Retrieved sources:")
            for source in result.sources:
                print(f"  - Chunk {source.chunk_index}: {source.content}")

        overall_accuracy = passed_cases / total_cases if total_cases else 0.0

        retrieval_accuracy = retrieval_passes / total_cases if total_cases else 0.0

        answer_accuracy = answer_passes / total_cases if total_cases else 0.0

        print("\n" + "=" * 50)
        print(f"Overall:   {passed_cases}/{total_cases} ({overall_accuracy:.2%})")
        print(f"Retrieval: {retrieval_passes}/{total_cases} ({retrieval_accuracy:.2%})")
        print(f"Answers:   {answer_passes}/{total_cases} ({answer_accuracy:.2%})")

    finally:
        if document is not None:
            database_session.delete(document)
            database_session.commit()

        database_session.close()


if __name__ == "__main__":
    run_rag_eval()
