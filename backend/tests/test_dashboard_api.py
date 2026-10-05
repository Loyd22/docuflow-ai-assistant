"""
API integration tests for dashboard operations.

These tests check dashboard totals, grouped counts,
and role-based access.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import (
    DocumentStatus,
    DocumentType,
    UserRole,
    WorkflowStatus,
)
from app.db.models.document import Document
from app.db.models.user import User
from app.db.models.workflow import Workflow


def create_test_user_and_token(
    client: TestClient,
    db_session: Session,
    *,
    name: str,
    email: str,
    role: UserRole,
) -> tuple[User, str]:
    """Create a user and return its login token."""

    register_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user = db_session.query(User).filter(User.email == email).one()

    # Give the user the role needed for this test.
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

    access_token = login_response.json()["access_token"]

    return user, access_token


def create_test_document(
    db_session: Session,
    *,
    uploaded_by: int,
    file_number: int,
    document_type: DocumentType,
    status: DocumentStatus,
) -> Document:
    """Create a document for dashboard testing."""

    document = Document(
        uploaded_by=uploaded_by,
        original_file_name=f"dashboard-{file_number}.txt",
        stored_file_name=f"dashboard-{file_number}-stored.txt",
        file_path=f"uploads/dashboard-{file_number}-stored.txt",
        mime_type="text/plain",
        file_size=100,
        document_type=document_type,
        status=status,
        extracted_text="Dashboard test document.",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    return document


def create_test_workflow(
    db_session: Session,
    *,
    document_id: int,
    status: WorkflowStatus,
) -> Workflow:
    """Create a workflow for dashboard testing."""

    workflow = Workflow(
        document_id=document_id,
        current_status=status,
        recommended_action="manager_review",
    )

    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)

    return workflow


def test_manager_can_view_dashboard_summary(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to view dashboard data."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Dashboard Manager",
        email="dashboard-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200


def test_admin_can_view_dashboard_summary(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should be able to view dashboard data."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Dashboard Admin",
        email="dashboard-admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200


def test_employee_cannot_view_dashboard_summary(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should not be allowed to view the dashboard."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Dashboard Employee",
        email="dashboard-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action."
    )


def test_dashboard_returns_correct_document_counts(
    client: TestClient,
    db_session: Session,
) -> None:
    """Dashboard should count documents by status and type."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Document Count Manager",
        email="document-count-manager@example.com",
        role=UserRole.MANAGER,
    )

    create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=1,
        document_type=DocumentType.INVOICE,
        status=DocumentStatus.ANALYZED,
    )

    create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=2,
        document_type=DocumentType.INVOICE,
        status=DocumentStatus.ANALYZED,
    )

    create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=3,
        document_type=DocumentType.CONTRACT,
        status=DocumentStatus.UPLOADED,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_documents"] == 3

    assert data["documents_by_status"]["analyzed"] == 2
    assert data["documents_by_status"]["uploaded"] == 1

    assert data["documents_by_type"]["invoice"] == 2
    assert data["documents_by_type"]["contract"] == 1


def test_dashboard_returns_correct_workflow_counts(
    client: TestClient,
    db_session: Session,
) -> None:
    """Dashboard should count workflows by status."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow Count Manager",
        email="workflow-count-manager@example.com",
        role=UserRole.MANAGER,
    )

    document_one = create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=4,
        document_type=DocumentType.INVOICE,
        status=DocumentStatus.ANALYZED,
    )

    document_two = create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=5,
        document_type=DocumentType.INVOICE,
        status=DocumentStatus.ANALYZED,
    )

    document_three = create_test_document(
        db_session,
        uploaded_by=manager.id,
        file_number=6,
        document_type=DocumentType.CONTRACT,
        status=DocumentStatus.ANALYZED,
    )

    create_test_workflow(
        db_session,
        document_id=document_one.id,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    create_test_workflow(
        db_session,
        document_id=document_two.id,
        status=WorkflowStatus.APPROVED,
    )

    create_test_workflow(
        db_session,
        document_id=document_three.id,
        status=WorkflowStatus.APPROVED,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_workflows"] == 3
    assert data["workflows_by_status"]["pending_approval"] == 1
    assert data["workflows_by_status"]["approved"] == 2


def test_dashboard_returns_zero_for_missing_categories(
    client: TestClient,
    db_session: Session,
) -> None:
    """Missing dashboard categories should return zero."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Empty Dashboard Manager",
        email="empty-dashboard-manager@example.com",
        role=UserRole.MANAGER,
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_documents"] == 0
    assert data["total_workflows"] == 0

    assert data["documents_by_status"]["analyzed"] == 0
    assert data["documents_by_type"]["invoice"] == 0
    assert data["workflows_by_status"]["approved"] == 0
