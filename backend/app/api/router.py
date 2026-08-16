"""
Main API router.

Every feature router will eventually be registered here.
"""

from fastapi import APIRouter

from app.api.routes.health_routes import router as health_router


api_router = APIRouter()

# Register the health-check endpoints.
api_router.include_router(health_router)