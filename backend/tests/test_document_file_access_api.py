"""Integration tests for original document viewing and downloading."""

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import DocumentStatus, UserRole, WorkflowStatus
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow
from app.storage import file_storage


@pytest.fixture(autouse=True)
def isolate_uploaded_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep test documents outside the real uploads folder."""

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIRECTORY",
        tmp_path,
    )


def create_test_user(
    client: TestClient,
    db_session: Session,
    *,
    email: str,
    role: UserRole = UserRole.EMPLOYEE,
) -> tuple[str, User]:
    """Register a user and return their JWT and database record."""

    register_response = client.post(
        "/auth/register",
        json={
            "name": "File Access Tester",
            "email": email,
            "password": "password123",
        },
    )
    assert register_response.status_code == 201

    user = db_session.query(User).filter(User.email == email).one()

    user.role = role
    db_session.commit()
    db_session.refresh(user)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"], user


def upload_test_document(
    client: TestClient,
    *,
    token: str,
    filename: str = "invoice.txt",
    content: bytes = b"Invoice Number: INV-001\nTotal: PHP 15000",
) -> int:
    """Upload a real file through the document API."""

    response = client.post(
        "/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "uploaded_file": (
                filename,
                content,
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def auth_headers(token: str) -> dict[str, str]:
    """Attach the authenticated user's JWT."""

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("action", ["view", "download"])
def test_owner_can_access_original_file(
    client: TestClient,
    db_session: Session,
    action: str,
) -> None:
    """Employees can retrieve files they uploaded."""

    token, _ = create_test_user(
        client,
        db_session,
        email=f"file-owner-{action}@example.com",
    )

    content = b"Invoice Number: INV-001\nTotal: PHP 15000"

    document_id = upload_test_document(
        client,
        token=token,
        content=content,
    )

    response = client.get(
        f"/documents/{document_id}/{action}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.content == content
    assert response.headers["x-content-type-options"] == "nosniff"

    disposition = response.headers["content-disposition"]

    if action == "view":
        assert disposition.startswith("inline;")
    else:
        assert disposition.startswith("attachment;")

    assert "invoice.txt" in disposition


@pytest.mark.parametrize("action", ["view", "download"])
def test_employee_cannot_access_another_users_file(
    client: TestClient,
    db_session: Session,
    action: str,
) -> None:
    """An employee cannot retrieve another employee's file."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email=f"private-owner-{action}@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    other_token, _ = create_test_user(
        client,
        db_session,
        email=f"other-employee-{action}@example.com",
    )

    response = client.get(
        f"/documents/{document_id}/{action}",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403


@pytest.mark.parametrize("action", ["view", "download"])
def test_original_file_requires_authentication(
    client: TestClient,
    action: str,
) -> None:
    """Anonymous users cannot retrieve original files."""

    response = client.get(f"/documents/1/{action}")

    assert response.status_code == 401


@pytest.mark.parametrize("action", ["view", "download"])
def test_unknown_document_returns_404(
    client: TestClient,
    db_session: Session,
    action: str,
) -> None:
    """A missing document ID must return 404."""

    token, _ = create_test_user(
        client,
        db_session,
        email=f"missing-record-{action}@example.com",
    )

    response = client.get(
        f"/documents/999999/{action}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_missing_physical_file_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    """An existing database record may point to a missing file."""

    token, _ = create_test_user(
        client,
        db_session,
        email="missing-physical-file@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
    )

    document = db_session.get(Document, document_id)
    assert document is not None

    stored_path = file_storage.get_stored_file_path(
        document.stored_file_name,
    )

    stored_path.unlink()

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_invalid_stored_filename_returns_500(
    client: TestClient,
    db_session: Session,
) -> None:
    """Invalid internal storage paths cannot be served."""

    token, _ = create_test_user(
        client,
        db_session,
        email="invalid-stored-path@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
    )

    document = db_session.get(Document, document_id)
    assert document is not None

    document.stored_file_name = "../secret.txt"
    db_session.commit()

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(token),
    )

    assert response.status_code == 500
    assert response.json()["detail"] == ("Original document storage is invalid.")


def test_docx_preview_is_not_supported(
    client: TestClient,
    db_session: Session,
) -> None:
    """DOCX files must be downloaded instead of previewed."""

    token, _ = create_test_user(
        client,
        db_session,
        email="docx-preview@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
        filename="contract.docx",
        content=b"Sample DOCX file for access testing",
    )

    response = client.get(
        f"/documents/{document_id}/view",
        headers=auth_headers(token),
    )

    assert response.status_code == 415


def test_docx_can_be_downloaded(
    client: TestClient,
    db_session: Session,
) -> None:
    """DOCX originals can still be downloaded."""

    token, _ = create_test_user(
        client,
        db_session,
        email="docx-download@example.com",
    )

    content = b"Sample DOCX file for access testing"

    document_id = upload_test_document(
        client,
        token=token,
        filename="contract.docx",
        content=content,
    )

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.content == content

    assert response.headers["content-disposition"].startswith("attachment;")


def test_manager_can_access_shared_review_document(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers can access unassigned shared-review workflows."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email="shared-review-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    workflow = Workflow(
        document_id=document_id,
        current_status=WorkflowStatus.NEEDS_REVIEW,
        assigned_to=None,
    )

    db_session.add(workflow)
    db_session.commit()

    manager_token, _ = create_test_user(
        client,
        db_session,
        email="shared-review-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        f"/documents/{document_id}/view",
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 200


def test_manager_cannot_access_unassigned_nonreview_document(
    client: TestClient,
    db_session: Session,
) -> None:
    """A manager cannot access unrelated completed workflows."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email="completed-file-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    workflow = Workflow(
        document_id=document_id,
        current_status=WorkflowStatus.COMPLETED,
        assigned_to=None,
    )

    db_session.add(workflow)
    db_session.commit()

    manager_token, _ = create_test_user(
        client,
        db_session,
        email="unassigned-file-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 403


def test_assigned_manager_can_download_document(
    client: TestClient,
    db_session: Session,
) -> None:
    """An assigned manager can retrieve the workflow's original."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email="assigned-file-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    manager_token, manager = create_test_user(
        client,
        db_session,
        email="assigned-file-manager@example.com",
        role=UserRole.MANAGER,
    )

    workflow = Workflow(
        document_id=document_id,
        current_status=WorkflowStatus.PENDING_APPROVAL,
        assigned_to=manager.id,
    )

    db_session.add(workflow)
    db_session.commit()

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 200


def test_other_manager_cannot_access_assigned_document(
    client: TestClient,
    db_session: Session,
) -> None:
    """An assignment must not grant access to other managers."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email="restricted-file-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    _, assigned_manager = create_test_user(
        client,
        db_session,
        email="restricted-assignee@example.com",
        role=UserRole.MANAGER,
    )

    workflow = Workflow(
        document_id=document_id,
        current_status=WorkflowStatus.NEEDS_REVIEW,
        assigned_to=assigned_manager.id,
    )

    db_session.add(workflow)
    db_session.commit()

    other_token, _ = create_test_user(
        client,
        db_session,
        email="restricted-other-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        f"/documents/{document_id}/view",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403


def test_admin_can_download_another_users_document(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins may retrieve originals across document ownership."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email="admin-file-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    admin_token, _ = create_test_user(
        client,
        db_session,
        email="original-file-admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200


def test_manager_cannot_access_document_without_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers cannot read another user's document without a workflow."""

    # An employee uploads a document.
    owner_token, _ = create_test_user(
        client,
        db_session,
        email="no-workflow-owner@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
    )

    # Confirm the document has no associated workflow.
    document = db_session.get(Document, document_id)
    assert document is not None
    assert document.workflow is None

    # A manager attempts to access the employee's original file.
    manager_token, _ = create_test_user(
        client,
        db_session,
        email="no-workflow-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        f"/documents/{document_id}/download",
        headers=auth_headers(manager_token),
    )

    # A manager has no automatic access to unrelated uploads.
    assert response.status_code == 403


@pytest.mark.parametrize("action", ["view", "download"])
def test_file_response_cleans_up_temporary_file(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    action: str,
) -> None:
    """Clean up temporary files after sending the response."""

    token, _ = create_test_user(
        client,
        db_session,
        email=f"cleanup-{action}@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
    )

    temporary_file = tmp_path / f"temporary-{action}.txt"
    content = b"Private temporary document"
    temporary_file.write_bytes(content)

    authorized_file = MagicMock()
    authorized_file.path = temporary_file
    authorized_file.original_file_name = "invoice.txt"
    authorized_file.mime_type = "text/plain"

    def cleanup() -> None:
        """Remove the temporary file."""
        temporary_file.unlink(missing_ok=True)

    authorized_file.cleanup.side_effect = cleanup

    with patch(
        "app.api.routes.document_routes.get_authorized_original_file",
        return_value=authorized_file,
    ):
        response = client.get(
            f"/documents/{document_id}/{action}",
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    assert response.content == content
    authorized_file.cleanup.assert_called_once()
    assert not temporary_file.exists()


def test_docx_preview_rejection_cleans_up_temporary_file(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    """Clean up a temporary DOCX when preview is rejected."""

    token, _ = create_test_user(
        client,
        db_session,
        email="cleanup-docx-preview@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
        filename="contract.docx",
    )

    temporary_file = tmp_path / "temporary-contract.docx"
    temporary_file.write_bytes(b"Temporary document")

    authorized_file = MagicMock()
    authorized_file.path = temporary_file
    authorized_file.original_file_name = "contract.docx"
    authorized_file.mime_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    authorized_file.cleanup.side_effect = lambda: temporary_file.unlink(missing_ok=True)

    with patch(
        "app.api.routes.document_routes.get_authorized_original_file",
        return_value=authorized_file,
    ):
        response = client.get(
            f"/documents/{document_id}/view",
            headers=auth_headers(token),
        )

    assert response.status_code == 415
    authorized_file.cleanup.assert_called_once()
    assert not temporary_file.exists()


def test_document_lifecycle_uses_configured_storage(
    client: TestClient,
    db_session: Session,
) -> None:
    """Upload, process, view, and download the same document."""

    token, _ = create_test_user(
        client,
        db_session,
        email="storage-lifecycle@example.com",
    )

    content = b"DocuFlow storage lifecycle integration test."

    # Upload using the configured storage provider.
    document_id = upload_test_document(
        client,
        token=token,
        filename="lifecycle.txt",
        content=content,
    )

    headers = auth_headers(token)

    # Extract text from the uploaded document.
    process_response = client.post(
        f"/documents/{document_id}/process",
        headers=headers,
    )

    assert process_response.status_code == 200
    assert process_response.json()["status"] == "text_extracted"

    # Verify the extracted text was saved in PostgreSQL.
    db_session.expire_all()

    processed_document = db_session.get(Document, document_id)

    assert processed_document is not None
    assert processed_document.status == DocumentStatus.TEXT_EXTRACTED
    assert processed_document.extracted_text == content.decode()

    # Preview the original document.
    view_response = client.get(
        f"/documents/{document_id}/view",
        headers=headers,
    )

    assert view_response.status_code == 200
    assert view_response.content == content
    assert view_response.headers["content-disposition"].startswith("inline;")

    # Download the original document.
    download_response = client.get(
        f"/documents/{document_id}/download",
        headers=headers,
    )

    assert download_response.status_code == 200
    assert download_response.content == content
    assert download_response.headers["content-disposition"].startswith("attachment;")

    # Confirm the original file remains stored.
    document = db_session.get(Document, document_id)

    assert document is not None

    stored_path = file_storage.get_stored_file_path(
        document.stored_file_name,
    )

    assert stored_path.read_bytes() == content


@pytest.mark.parametrize("endpoint", ["view", "download"])
@pytest.mark.parametrize(
    ("document_provider", "default_provider"),
    [
        ("local", "supabase"),
        ("supabase", "local"),
    ],
)
def test_file_access_uses_document_storage_provider(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    document_provider: str,
    default_provider: str,
) -> None:
    """Retrieve documents using their saved provider."""

    from app.core.config import settings

    token, _ = create_test_user(
        client,
        db_session,
        email=(f"mixed-{document_provider}-{endpoint}@example.com"),
    )

    content = b"Provider-specific document content"

    document_id = upload_test_document(
        client,
        token=token,
        filename="provider-test.txt",
        content=content,
    )

    # Simulate an existing document stored by this provider.
    document = db_session.get(Document, document_id)

    assert document is not None

    document.storage_provider = document_provider
    db_session.commit()

    # The application default is intentionally different.
    monkeypatch.setattr(
        settings,
        "storage_provider",
        default_provider,
    )

    storage = MagicMock()

    # Simulate downloading the original file.
    storage.download_to_path.side_effect = lambda key, destination: (
        destination.write_bytes(content)
    )

    with patch(
        "app.api.routes.document_routes.get_document_storage_for_provider",
        return_value=storage,
    ) as resolver:
        response = client.get(
            f"/documents/{document_id}/{endpoint}",
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    assert response.content == content

    # The persisted provider must win over the default.
    resolver.assert_called_once_with(document_provider)

    storage.download_to_path.assert_called_once()


@pytest.mark.parametrize("endpoint", ["view", "download"])
def test_unauthorized_file_access_never_resolves_provider(
    client: TestClient,
    db_session: Session,
    endpoint: str,
) -> None:
    """Unauthorized users cannot initialize document storage."""

    owner_token, _ = create_test_user(
        client,
        db_session,
        email=f"storage-owner-{endpoint}@example.com",
    )

    other_token, _ = create_test_user(
        client,
        db_session,
        email=f"storage-other-{endpoint}@example.com",
    )

    document_id = upload_test_document(
        client,
        token=owner_token,
        filename="private.txt",
        content=b"Confidential document",
    )

    document = db_session.get(Document, document_id)

    assert document is not None

    document.storage_provider = "supabase"
    db_session.commit()

    with patch(
        "app.api.routes.document_routes.get_document_storage_for_provider",
    ) as resolver:
        response = client.get(
            f"/documents/{document_id}/{endpoint}",
            headers=auth_headers(other_token),
        )

    assert response.status_code == 403

    # Authorization must happen before cloud initialization.
    resolver.assert_not_called()


@pytest.mark.parametrize("endpoint", ["view", "download"])
def test_missing_supabase_object_returns_404(
    client: TestClient,
    db_session: Session,
    endpoint: str,
) -> None:
    """Return 404 when a cloud document's original object is missing."""

    token, _ = create_test_user(
        client,
        db_session,
        email=f"missing-cloud-{endpoint}@example.com",
    )

    # Create a document using the existing test upload helper.
    document_id = upload_test_document(
        client,
        token=token,
        filename="missing-cloud.txt",
        content=b"Temporary test document.",
    )

    document = db_session.get(Document, document_id)
    assert document is not None

    # Simulate a document originally stored in Supabase.
    document.storage_provider = "supabase"
    db_session.commit()

    storage = MagicMock()

    # Simulate the adapter reporting a missing cloud object.
    storage.download_to_path.side_effect = FileNotFoundError(
        "Original document file not found."
    )

    with patch(
        "app.api.routes.document_routes.get_document_storage_for_provider",
        return_value=storage,
    ) as resolver:
        response = client.get(
            f"/documents/{document_id}/{endpoint}",
            headers=auth_headers(token),
        )

    assert response.status_code == 404
    assert response.json()["detail"] == ("Original document file not found.")

    # Confirm the document's recorded provider was selected.
    resolver.assert_called_once_with("supabase")

    # Confirm that retrieval was actually attempted.
    storage.download_to_path.assert_called_once_with(
        document.stored_file_name,
        ANY,
    )


@pytest.mark.parametrize("endpoint", ["view", "download"])
def test_supabase_outage_returns_safe_error(
    client: TestClient,
    db_session: Session,
    endpoint: str,
) -> None:
    """A cloud outage must not expose internal error details."""

    token, _ = create_test_user(
        client,
        db_session,
        email=f"cloud-outage-{endpoint}@example.com",
    )

    document_id = upload_test_document(
        client,
        token=token,
        filename="outage-test.txt",
        content=b"Cloud outage testing.",
    )

    document = db_session.get(Document, document_id)
    assert document is not None

    # Simulate an existing cloud-backed document.
    document.storage_provider = "supabase"
    db_session.commit()

    storage = MagicMock()

    # Simulate an unexpected cloud storage failure.
    sensitive_error = (
        "Supabase connection failed: authorization=Bearer example-sensitive-token"
    )

    storage.download_to_path.side_effect = RuntimeError(sensitive_error)

    with patch(
        "app.api.routes.document_routes.get_document_storage_for_provider",
        return_value=storage,
    ) as resolver:
        response = client.get(
            f"/documents/{document_id}/{endpoint}",
            headers=auth_headers(token),
        )

    # The API must return a controlled server error.
    assert response.status_code == 500

    assert response.json()["detail"] == ("Original document storage is invalid.")

    # Never expose internal SDK errors in the HTTP response.
    assert "example-sensitive-token" not in response.text
    assert "authorization" not in response.text.lower()

    resolver.assert_called_once_with("supabase")
    storage.download_to_path.assert_called_once()

    # Cloud failures must not modify document metadata.
    db_session.refresh(document)

    assert document.storage_provider == "supabase"
    assert document.status.value == "uploaded"
