from fastapi import APIRouter

from app.api.routes.auth_routes import router as auth_router
from app.api.routes.health_routes import router as health_router

# Central API router.
# Feature-specific routers are registered here so main.py
# does not need to know about every individual route module.
api_router = APIRouter()


# Health endpoints
api_router.include_router(health_router)


# Authentication endpoints:
# POST /auth/register
# POST /auth/login
# GET  /auth/me
api_router.include_router(auth_router)
