from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health_routes


# This creates the FastAPI application.
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)


# This allows the frontend to communicate with the backend.
# During development, React usually runs on localhost:5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# This registers the health route.
app.include_router(health_routes.router)


@app.get("/")
def root():
    # This is the root endpoint.
    return {
        "message": "Welcome to DocuFlow AI API"
    }