"""Opt-in end-to-end FastAPI and Supabase Storage test."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document
from app.storage.factory import get_document_storage_for_provider


@pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_STORAGE_LIVE_TESTS") != "1",
    reason="Live Supabase Storage tests are disabled.",
)
def test_live_supabase_document_api_workflow(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload, processing, preview, and download using Supabase."""

    if not settings.supabase_url or not settings.supabase_secret_key:
        pytest.fail("Supabase credentials are not configured.")

    # Use Supabase only during this test.
    monkeypatch.setattr(settings, "storage_provider", "supabase")

    # Create a unique user and filename for this test.
    identifier = uuid4().hex
    email = f"cloud-test-{identifier}@example.com"
    filename = f"cloud-document-{identifier}.txt"
    content = b"DocuFlow live cloud document processing test."

    # Register a temporary test user.
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Cloud Test User",
            "email": email,
            "password": "password123",
        },
    )
    assert register_response.status_code == 201

    # Authenticate the test user.
    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Initialize the real storage adapter for cleanup.
    storage = get_document_storage_for_provider("supabase")
    storage_key = None

    try:
        # Upload through the real FastAPI endpoint.
        upload_response = client.post(
            "/documents",
            headers=headers,
            files={
                "uploaded_file": (
                    filename,
                    content,
                    "text/plain",
                ),
            },
        )

        assert upload_response.status_code == 201

        document_id = upload_response.json()["id"]

        # Verify that PostgreSQL recorded Supabase as the provider.
        document = db_session.get(Document, document_id)
        assert document is not None

        storage_key = document.file_path

        assert document.storage_provider == "supabase"
        assert document.original_file_name == filename
        assert document.status.value == "uploaded"

        # Process the document using its saved provider.
        process_response = client.post(
            f"/documents/{document_id}/process",
            headers=headers,
        )

        assert process_response.status_code == 200
        assert process_response.json()["status"] == "text_extracted"

        db_session.refresh(document)

        assert document.status.value == "text_extracted"
        assert document.extracted_text == content.decode("utf-8")

        # Preview through the authenticated API.
        view_response = client.get(
            f"/documents/{document_id}/view",
            headers=headers,
        )

        assert view_response.status_code == 200
        assert view_response.content == content

        # Download through the authenticated API.
        download_response = client.get(
            f"/documents/{document_id}/download",
            headers=headers,
        )

        assert download_response.status_code == 200
        assert download_response.content == content

    finally:
        # Only delete the cloud object recorded for this test.
        if storage_key is not None:
            storage.delete(storage_key)
