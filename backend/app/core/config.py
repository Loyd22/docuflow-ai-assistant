from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # This is the application name shown in FastAPI docs.
    APP_NAME: str = "DocuFlow AI"

    # This tells us if we are running in development, testing, or production.
    APP_ENV: str = "development"

    # This is the database connection string.
    DATABASE_URL: str

    # This is used later for JWT authentication.
    JWT_SECRET_KEY: str

    # This is the algorithm used for JWT tokens.
    JWT_ALGORITHM: str = "HS256"

    # This controls how long login tokens stay valid.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # This is the folder where uploaded documents will be stored.
    UPLOAD_DIR: str = "uploads"

    # This tells the app which AI provider to use later.
    LLM_PROVIDER: str = "openai"

    class Config:
        # This tells Pydantic to read values from the .env file.
        env_file = ".env"


# This creates one settings object that we can import anywhere.
settings = Settings()