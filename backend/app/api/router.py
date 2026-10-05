"""
Main API router.

Every feature router will eventually be registered here.
"""

from fastapi import APIRouter

from app.api.routes import (
    audit_log_routes,
    auth_routes,
    dashboard_routes,
    document_routes,
    health_routes,
    workflow_routes,
)

api_router = APIRouter()

# Add all feature routes to the main API.
api_router.include_router(health_routes.router)
api_router.include_router(auth_routes.router)
api_router.include_router(document_routes.router)
api_router.include_router(workflow_routes.router)
api_router.include_router(audit_log_routes.router)
api_router.include_router(dashboard_routes.router)
