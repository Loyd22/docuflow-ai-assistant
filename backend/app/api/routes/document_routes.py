"""
Document API endpoints.

These routes handle HTTP concerns for document operations
and delegate business logic to the document service layer.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.processing.exceptions import DocumentProcessingError
from app.repositories.document_repository import get_document_by_id
from app.schemas.document_schema import DocumentResponse
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
