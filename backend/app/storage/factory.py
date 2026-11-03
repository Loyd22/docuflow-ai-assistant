"""Select and create document storage providers."""

from typing import Literal

from app.core.config import settings
from app.storage.base import DocumentStorage
from app.storage.local_storage import LocalDocumentStorage
from app.storage.supabase_storage import SupabaseDocumentStorage

StorageProviderName = Literal["local", "supabase"]


def get_document_storage_for_provider(
    provider: StorageProviderName,
) -> DocumentStorage:
    """Return the adapter for a specific storage provider."""

    if provider == "local":
        return LocalDocumentStorage()

    if provider == "supabase":
        from supabase import create_client

        if not settings.supabase_url or not settings.supabase_secret_key:
            raise ValueError("Supabase Storage credentials are missing.")

        client = create_client(
            settings.supabase_url,
            settings.supabase_secret_key,
        )

        return SupabaseDocumentStorage(
            client=client,
            bucket_name=settings.supabase_storage_bucket,
        )

    raise ValueError(f"Unsupported storage provider: {provider}")


def get_document_storage() -> DocumentStorage:
    """Return storage for new uploads using application settings."""

    return get_document_storage_for_provider(settings.storage_provider)
