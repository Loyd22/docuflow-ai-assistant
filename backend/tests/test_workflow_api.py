"""
API integration tests for workflow and approval operations.

These tests verify that the FastAPI workflow endpoints correctly handle:
- authenticated workflow retrieval
- missing workflows
- manager/admin authorization
- approval persistence
- workflow state transitions
- invalid workflow-state decisions

The tests use the real PostgreSQL test database.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import (
    ApprovalDecision,
    DocumentStatus,
    DocumentType,
    UserRole,
    WorkflowStatus,
)
from app.db.models.approval import Approval
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
    """Create a user, assign a role, and return an access token."""

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
) -> Document:
    """Create a minimal analyzed document for workflow tests."""

    stored_file_name = f"workflow-test-stored-{uploaded_by}.txt"

    document = Document(
        uploaded_by=uploaded_by,
        original_file_name="workflow-test.txt",
        stored_file_name=stored_file_name,
        file_path=f"uploads/{stored_file_name}",
        mime_type="text/plain",
        file_size=100,
        document_type=DocumentType.INVOICE,
        status=DocumentStatus.ANALYZED,
        extracted_text="Total Amount: 25000.00",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    return document


def create_test_workflow(
    db_session: Session,
    *,
    document_id: int,
    status: WorkflowStatus = WorkflowStatus.PENDING_APPROVAL,
) -> Workflow:
    """Create a workflow for API testing."""

    workflow = Workflow(
        document_id=document_id,
        current_status=status,
        recommended_action="manager_review",
    )

    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)

    return workflow


def test_get_workflow_returns_existing_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Authenticated users should be able to retrieve an existing workflow."""

    user, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow Employee",
        email="workflow-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    document = create_test_document(
        db_session,
        uploaded_by=user.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.get(
        f"/workflows/{workflow.id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == workflow.id
    assert response_data["document_id"] == document.id
    assert response_data["current_status"] == "pending_approval"
    assert response_data["recommended_action"] == "manager_review"


def test_get_workflow_returns_not_found(
    client: TestClient,
    db_session: Session,
) -> None:
    """Unknown workflow IDs should return 404."""

    _, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Lookup Employee",
        email="lookup-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    response = client.get(
        "/workflows/999999",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found."


def test_employee_cannot_submit_workflow_decision(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should not be allowed to approve workflows."""

    employee, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Decision Employee",
        email="decision-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "approved",
            "comment": "Employee should not be allowed.",
        },
    )

    assert response.status_code == 403

    db_session.refresh(workflow)

    assert workflow.current_status == WorkflowStatus.PENDING_APPROVAL

    approvals = (
        db_session.query(Approval).filter(Approval.workflow_id == workflow.id).all()
    )

    assert approvals == []


def test_manager_can_approve_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to approve pending workflows."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Approval Manager",
        email="approval-manager@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=manager.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "approved",
            "comment": "Approved for payment.",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["workflow"]["current_status"] == "approved"
    assert response_data["approval"]["decision"] == "approved"
    assert response_data["approval"]["approver_id"] == manager.id
    assert response_data["approval"]["comment"] == "Approved for payment."

    db_session.expire_all()

    persisted_workflow = db_session.get(
        Workflow,
        workflow.id,
    )

    assert persisted_workflow is not None
    assert persisted_workflow.current_status == WorkflowStatus.APPROVED

    persisted_approval = (
        db_session.query(Approval).filter(Approval.workflow_id == workflow.id).one()
    )

    assert persisted_approval.approver_id == manager.id
    assert persisted_approval.decision == ApprovalDecision.APPROVED
    assert persisted_approval.comment == "Approved for payment."


def test_admin_can_approve_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should also be allowed to approve pending workflows."""

    admin, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow Admin",
        email="workflow-admin@example.com",
        role=UserRole.ADMIN,
    )

    document = create_test_document(
        db_session,
        uploaded_by=admin.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "approved",
            "comment": "Approved by admin.",
        },
    )

    assert response.status_code == 200
    assert response.json()["workflow"]["current_status"] == "approved"


def test_manager_can_reject_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Rejected decisions should move workflows to rejected."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Reject Manager",
        email="reject-manager@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=manager.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "rejected",
            "comment": "Invoice details do not match.",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["workflow"]["current_status"] == "rejected"
    assert response_data["approval"]["decision"] == "rejected"

    db_session.expire_all()

    persisted_workflow = db_session.get(
        Workflow,
        workflow.id,
    )

    assert persisted_workflow is not None
    assert persisted_workflow.current_status == WorkflowStatus.REJECTED


def test_manager_can_request_information(
    client: TestClient,
    db_session: Session,
) -> None:
    """Information requests should move workflows to needs-information."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Manager",
        email="information-manager@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=manager.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "information_requested",
            "comment": "Please provide the purchase order.",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["workflow"]["current_status"] == "needs_information"

    assert response_data["approval"]["decision"] == "information_requested"

    db_session.expire_all()

    persisted_workflow = db_session.get(
        Workflow,
        workflow.id,
    )

    assert persisted_workflow is not None
    assert persisted_workflow.current_status == WorkflowStatus.NEEDS_INFORMATION


def test_decision_on_non_pending_workflow_returns_conflict(
    client: TestClient,
    db_session: Session,
) -> None:
    """Decisions should be rejected when a workflow is not pending approval."""

    manager, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Conflict Manager",
        email="conflict-manager@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=manager.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=WorkflowStatus.COMPLETED,
    )

    response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "decision": "approved",
            "comment": "This should fail.",
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == ("Workflow is not waiting for approval.")

    db_session.refresh(workflow)

    assert workflow.current_status == WorkflowStatus.COMPLETED

    approvals = (
        db_session.query(Approval).filter(Approval.workflow_id == workflow.id).all()
    )

    assert approvals == []


def test_employee_cannot_view_another_users_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should not view workflows belonging to another user's document."""

    owner, _ = create_test_user_and_token(
        client,
        db_session,
        name="Workflow Owner",
        email="workflow-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    other_employee, access_token = create_test_user_and_token(
        client,
        db_session,
        name="Other Employee",
        email="other-workflow-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    document = create_test_document(
        db_session,
        uploaded_by=owner.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.get(
        f"/workflows/{workflow.id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("You are not allowed to view this workflow.")

    assert other_employee.id != owner.id


def test_manager_can_view_another_users_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to view workflows belonging to other users."""

    owner, _ = create_test_user_and_token(
        client,
        db_session,
        name="Document Owner",
        email="manager-view-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Viewing Manager",
        email="viewing-manager@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=owner.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.get(
        f"/workflows/{workflow.id}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == workflow.id


def test_admin_can_view_another_users_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should be able to view workflows belonging to other users."""

    owner, _ = create_test_user_and_token(
        client,
        db_session,
        name="Admin View Owner",
        email="admin-view-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, admin_token = create_test_user_and_token(
        client,
        db_session,
        name="Viewing Admin",
        email="viewing-admin@example.com",
        role=UserRole.ADMIN,
    )

    document = create_test_document(
        db_session,
        uploaded_by=owner.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
    )

    response = client.get(
        f"/workflows/{workflow.id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == workflow.id


def test_employee_list_workflows_returns_only_own_workflows(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees should only see workflows for their own documents."""

    employee, employee_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow List Employee",
        email="workflow-list-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    other_employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Other Workflow Employee",
        email="other-workflow-list-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    own_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    other_document = create_test_document(
        db_session,
        uploaded_by=other_employee.id,
    )

    own_workflow = create_test_workflow(
        db_session,
        document_id=own_document.id,
    )

    other_workflow = create_test_workflow(
        db_session,
        document_id=other_document.id,
    )

    response = client.get(
        "/workflows",
        headers={
            "Authorization": f"Bearer {employee_token}",
        },
    )

    assert response.status_code == 200

    workflow_ids = {workflow["id"] for workflow in response.json()}

    assert own_workflow.id in workflow_ids
    assert other_workflow.id not in workflow_ids


def test_manager_list_workflows_returns_all_workflows(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers should be able to see workflows from all users."""

    employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Manager List Employee",
        email="manager-list-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow List Manager",
        email="workflow-list-manager@example.com",
        role=UserRole.MANAGER,
    )

    employee_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    employee_workflow = create_test_workflow(
        db_session,
        document_id=employee_document.id,
    )

    response = client.get(
        "/workflows",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert response.status_code == 200

    workflow_ids = {workflow["id"] for workflow in response.json()}

    assert employee_workflow.id in workflow_ids


def test_admin_list_workflows_returns_all_workflows(
    client: TestClient,
    db_session: Session,
) -> None:
    """Admins should be able to see workflows from all users."""

    employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Admin List Employee",
        email="admin-list-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, admin_token = create_test_user_and_token(
        client,
        db_session,
        name="Workflow List Admin",
        email="workflow-list-admin@example.com",
        role=UserRole.ADMIN,
    )

    employee_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    employee_workflow = create_test_workflow(
        db_session,
        document_id=employee_document.id,
    )

    response = client.get(
        "/workflows",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    workflow_ids = {workflow["id"] for workflow in response.json()}

    assert employee_workflow.id in workflow_ids


def test_list_workflows_requires_authentication(
    client: TestClient,
) -> None:
    """Workflow listing should require authentication."""

    response = client.get("/workflows")

    assert response.status_code == 401
