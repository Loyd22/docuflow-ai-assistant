"""
Document API endpoints.

These routes handle HTTP concerns for document operations
and delegate business logic to the document service layer.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.ai.classifier import DocumentClassifier
from app.ai.client import create_openai_client
from app.ai.exceptions import (
    AIClassificationError,
    AIConfigurationError,
    AIExtractionError,
)
from app.ai.extractor import InvoiceExtractor
from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.processing.exceptions import DocumentProcessingError
from app.repositories.document_repository import get_document_by_id
from app.schemas.document_schema import DocumentResponse
from app.services.document_ai_service import DocumentAIService
from app.services.document_analysis_service import DocumentAnalysisService
from app.services.document_processing_service import process_document
from app.services.document_service import upload_document

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

        # Coordinate classification and structured extraction.
        ai_service = DocumentAIService(
            classifier=classifier,
            invoice_extractor=invoice_extractor,
        )

        # Coordinate document state, persistence, and AI analysis.
        analysis_service = DocumentAnalysisService(
            database_session=database_session,
            ai_service=ai_service,
        )

        analyzed_document = analysis_service.analyze(document)

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
