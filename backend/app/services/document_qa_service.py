"""Service for answering questions about indexed documents."""

from sqlalchemy.orm import Session

from app.ai.qa_generator import DocumentQAGenerator
from app.schemas.document_schema import (
    DocumentQuestionResponse,
    DocumentQuestionSource,
)
from app.services.document_retrieval_service import (
    DocumentRetrievalService,
)


class DocumentQAService:
    """Coordinate document retrieval and grounded answer generation."""

    def __init__(
        self,
        retrieval_service: DocumentRetrievalService,
        qa_generator: DocumentQAGenerator,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.qa_generator = qa_generator

    def answer_question(
        self,
        database_session: Session,
        *,
        document_id: int,
        question: str,
        limit: int = 5,
    ) -> DocumentQuestionResponse:
        """Retrieve relevant context and answer a document question."""

        chunks = self.retrieval_service.retrieve(
            database_session,
            document_id=document_id,
            question=question,
            limit=limit,
        )

        if not chunks:
            return DocumentQuestionResponse(
                answer=(
                    "I could not find enough information in the document "
                    "to answer that question."
                ),
                sources=[],
            )

        context = "\n\n".join(chunk.content for chunk in chunks)

        answer = self.qa_generator.generate(
            question=question,
            context=context,
        )

        sources = [
            DocumentQuestionSource(
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )
            for chunk in chunks
        ]

        return DocumentQuestionResponse(
            answer=answer,
            sources=sources,
        )
