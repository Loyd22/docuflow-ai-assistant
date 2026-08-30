"""
DocuFlow FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Build and configure the FastAPI application."""

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
    )

    # Allow the local React development server to call FastAPI.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    return application


app = create_application()
