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
from app.schemas.document_schema import DocumentResponse
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
