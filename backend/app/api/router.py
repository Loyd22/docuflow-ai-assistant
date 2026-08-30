"""
Main API router.

Every feature router will eventually be registered here.
"""

from fastapi import APIRouter

from app.api.routes import auth_routes, document_routes, health_routes

api_router = APIRouter()

api_router.include_router(health_routes.router)
api_router.include_router(auth_routes.router)
api_router.include_router(document_routes.router)
