"""
Document API endpoints.

These routes handle HTTP concerns for document operations
and delegate business logic to the document service layer.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.ai.classifier import DocumentClassifier
from app.ai.client import create_openai_client
from app.ai.embedder import DocumentEmbedder
from app.ai.exceptions import (
    AIClassificationError,
    AIConfigurationError,
    AIEmbeddingError,
    AIExtractionError,
    AIQuestionAnsweringError,
)
from app.ai.extractor import InvoiceExtractor
from app.ai.qa_generator import DocumentQAGenerator
from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.processing.exceptions import DocumentProcessingError
from app.rag.chunker import TextChunker
from app.repositories.document_repository import get_document_by_id
from app.schemas.document_schema import (
    DocumentIndexResponse,
    DocumentQuestionRequest,
    DocumentQuestionResponse,
    DocumentResponse,
)
from app.services.document_ai_service import DocumentAIService
from app.services.document_analysis_service import DocumentAnalysisService
from app.services.document_chunking_service import DocumentChunkingService
from app.services.document_embedding_service import DocumentEmbeddingService
from app.services.document_indexing_service import DocumentIndexingService
from app.services.document_processing_service import process_document
from app.services.document_qa_service import DocumentQAService
from app.services.document_retrieval_service import DocumentRetrievalService
from app.services.document_service import upload_document
from app.services.workflow_service import WorkflowService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_upload(
    uploaded_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> DocumentResponse:
    """Upload a document for the authenticated user."""

    try:
        document = upload_document(
            database_session,
            uploaded_file=uploaded_file,
            uploaded_by=current_user.id,
        )

        return DocumentResponse.model_validate(document)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
)
def process_uploaded_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> DocumentResponse:
    """Process an uploaded document and extract its text."""

    document = get_document_by_id(
        database_session,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to process this document.",
        )

    try:
        processed_document = process_document(
            database_session,
            document,
        )

    except DocumentProcessingError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return DocumentResponse.model_validate(processed_document)


@router.post(
    "/{document_id}/analyze",
    response_model=DocumentResponse,
)
def analyze_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> DocumentResponse:
    """Run AI classification and structured extraction for a document."""

    document = get_document_by_id(
        database_session=database_session,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to analyze this document.",
        )

    try:
        # Create the shared OpenAI client.
        client = create_openai_client()

        # Create the document classifier.
        classifier = DocumentClassifier(
            client=client,
        )

        # Create the invoice-specific extractor.
        invoice_extractor = InvoiceExtractor(
            client=client,
        )

        # Coordinate Phase 9 workflow persistence and approval state.
        workflow_service = WorkflowService(
            database_session=database_session,
        )

        # Coordinate classification and structured extraction.
        ai_service = DocumentAIService(
            classifier=classifier,
            invoice_extractor=invoice_extractor,
        )

        # Coordinate document state, persistence, and AI analysis.
        analysis_service = DocumentAnalysisService(
            database_session=database_session,
            ai_service=ai_service,
            workflow_service=workflow_service,
        )

        analyzed_document, _ = analysis_service.analyze(document)

        return DocumentResponse.model_validate(analyzed_document)

    except ValueError as error:
        # The document is not currently valid for AI analysis.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except AIConfigurationError as error:
        # The AI provider is not configured correctly.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured.",
        ) from error

    except (
        AIClassificationError,
        AIExtractionError,
    ) as error:
        # An expected upstream AI operation failed.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document AI analysis failed.",
        ) from error


@router.post(
    "/{document_id}/ask",
    response_model=DocumentQuestionResponse,
)
def ask_document_question(
    document_id: int,
    request: DocumentQuestionRequest,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> DocumentQuestionResponse:
    """Answer a question using an indexed document."""

    document = get_document_by_id(
        database_session,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to ask questions about this document.",
        )

    try:
        client = create_openai_client()

        embedder = DocumentEmbedder(
            client=client,
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

        return qa_service.answer_question(
            database_session,
            document_id=document.id,
            question=request.question,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured.",
        ) from error

    except (
        AIEmbeddingError,
        AIQuestionAnsweringError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document question answering failed.",
        ) from error


@router.post(
    "/{document_id}/index",
    response_model=DocumentIndexResponse,
)
def index_document_for_rag(
    document_id: int,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db_session),
) -> DocumentIndexResponse:
    """Chunk and embed a processed document for RAG retrieval."""

    document = get_document_by_id(
        database_session,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to index this document.",
        )

    try:
        client = create_openai_client()

        chunker = TextChunker()

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

        indexed_chunks = indexing_service.index_document(
            database_session,
            document,
        )

        return DocumentIndexResponse(
            document_id=document.id,
            chunks_indexed=len(indexed_chunks),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured.",
        ) from error

    except AIEmbeddingError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document indexing failed.",
        ) from error
