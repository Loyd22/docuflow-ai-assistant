"""Integration tests for original document viewing and downloading."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import UserRole, WorkflowStatus
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
