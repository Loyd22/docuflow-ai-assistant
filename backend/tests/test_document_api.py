from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.document import Document


def register_and_login(
    client: TestClient,
    *,
    email: str = "uploader@example.com",
) -> str:
    """
    Register a test user and return a valid JWT access token.

    This helper keeps authentication setup out of individual
    document API tests.
    """

    register_response = client.post(
        "/auth/register",
        json={
            "name": "Document Uploader",
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_upload_document_success(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An authenticated user can upload a supported document."""

    # Redirect test uploads away from the real backend/uploads directory.
    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(client)

    response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "invoice.pdf",
                b"test invoice content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["original_file_name"] == "invoice.pdf"
    assert response_data["mime_type"] == "application/pdf"
    assert response_data["file_size"] == len(b"test invoice content")
    assert response_data["document_type"] == "unknown"
    assert response_data["status"] == "uploaded"

    assert isinstance(response_data["id"], int)
    assert isinstance(response_data["uploaded_by"], int)

    # Internal filesystem information must not be exposed by the API.
    assert "stored_file_name" not in response_data
    assert "file_path" not in response_data

    document = (
        db_session.query(Document).filter(Document.id == response_data["id"]).one()
    )

    assert document.original_file_name == "invoice.pdf"
    assert document.uploaded_by == response_data["uploaded_by"]

    # Verify that the physical file was actually stored.
    stored_file_path = Path(document.file_path)

    assert stored_file_path.exists()
    assert stored_file_path.read_bytes() == b"test invoice content"


def test_upload_document_requires_authentication(
    client: TestClient,
) -> None:
    """Anonymous users cannot upload documents."""

    response = client.post(
        "/documents",
        files={
            "uploaded_file": (
                "invoice.pdf",
                b"test invoice content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code in (401, 403)


def test_upload_document_rejects_unsupported_extension(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported file extensions must be rejected."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(client)

    response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "malware.exe",
                b"not allowed",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

    # Validation occurs before physical storage.
    assert list(tmp_path.iterdir()) == []


def test_upload_document_rejects_empty_file(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty documents must not be accepted."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(client)

    response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "empty.pdf",
                b"",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file cannot be empty."

    # The service should clean up the temporary saved file.
    assert list(tmp_path.iterdir()) == []


def test_upload_document_creates_database_record(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful upload metadata is persisted to PostgreSQL."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="database-check@example.com",
    )

    response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "company-policy.txt",
                b"Employees must follow company policy.",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 201

    document_id = response.json()["id"]

    document = db_session.query(Document).filter(Document.id == document_id).one()

    assert document.original_file_name == "company-policy.txt"
    assert document.mime_type == "text/plain"
    assert document.file_size == len(b"Employees must follow company policy.")
