# This file contains simple health-check routes for testing the backend.

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/health", tags=["Health"])


# This route checks if the backend is running.
@router.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "DocuFlow AI backend is running"
    }


# This route checks if the backend can connect to the database.
@router.get("/db")
def database_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "message": "Database connection is working"
    }