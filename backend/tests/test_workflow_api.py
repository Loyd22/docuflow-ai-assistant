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

from uuid import uuid4

import pytest
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
from app.db.models.workflow_information_request import (
    WorkflowInformationRequest,
)
from app.repositories.workflow_repository import get_workflow_by_id


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

    # Give every test document a unique stored filename.
    unique_id = uuid4().hex
    stored_file_name = f"workflow-test-{uploaded_by}-{unique_id}.txt"

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

    # Verify the request was saved and linked to the approval.
    information_request = (
        db_session.query(WorkflowInformationRequest)
        .filter(WorkflowInformationRequest.workflow_id == workflow.id)
        .one()
    )

    approval = (
        db_session.query(Approval).filter(Approval.workflow_id == workflow.id).one()
    )

    assert information_request.approval_id == approval.id
    assert information_request.review_id is None

    assert information_request.requested_by == manager.id
    assert information_request.request_comment == ("Please provide the purchase order.")

    assert information_request.return_status == "pending_approval"

    # The employee has not responded yet.
    assert information_request.response_comment is None
    assert information_request.responded_at is None


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


def test_manager_cannot_view_another_managers_assigned_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers cannot view workflows assigned to other managers."""

    # Create the employee who owns the document.
    employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Visibility Document Owner",
        email="visibility-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    # Create two different managers.
    assigned_manager, _ = create_test_user_and_token(
        client,
        db_session,
        name="Assigned Visibility Manager",
        email="assigned-visibility-manager@example.com",
        role=UserRole.MANAGER,
    )

    other_manager, other_token = create_test_user_and_token(
        client,
        db_session,
        name="Other Visibility Manager",
        email="other-visibility-manager@example.com",
        role=UserRole.MANAGER,
    )

    # Create a workflow assigned to the first manager.
    document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    workflow.assigned_to = assigned_manager.id
    db_session.commit()

    # Another manager attempts to view the assigned workflow.
    response = client.get(
        f"/workflows/{workflow.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert other_manager.id != assigned_manager.id

    # The API must reject unauthorized access.
    assert response.status_code == 403
    assert response.json()["detail"] == ("You are not allowed to view this workflow.")


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


# ---------------------------------------------------------
# Phase 12.5A - Manual-review API tests
# ---------------------------------------------------------


def create_test_manual_review_workflow(
    client: TestClient,
    db_session: Session,
    *,
    email: str,
    role: UserRole,
    workflow_status: WorkflowStatus = WorkflowStatus.NEEDS_REVIEW,
) -> tuple[Workflow, str]:
    """Create an invoice workflow and an authenticated reviewer."""

    user, token = create_test_user_and_token(
        client,
        db_session,
        name="Manual Review API User",
        email=email,
        role=role,
    )

    document = create_test_document(
        db_session,
        uploaded_by=user.id,
    )

    # Start with an invoice whose total is missing.
    document.extracted_data = {
        "invoice_number": "INV-REVIEW-001",
        "total_amount": None,
    }
    db_session.commit()

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=workflow_status,
    )

    return workflow, token


@pytest.mark.parametrize(
    ("role", "email"),
    [
        (UserRole.MANAGER, "review-api-manager@example.com"),
        (UserRole.ADMIN, "review-api-admin@example.com"),
    ],
)
def test_authorized_user_can_resolve_manual_review(
    client: TestClient,
    db_session: Session,
    role: UserRole,
    email: str,
) -> None:
    """Managers and admins can resolve invoice reviews."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email=email,
        role=role,
    )

    response = client.post(
        f"/workflows/{workflow.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "outcome": "resolved",
            "comment": "Verified the invoice total.",
            "corrected_total_amount": 5000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["workflow"]["current_status"] == "completed"
    assert data["review"]["outcome"] == "resolved"
    assert data["review"]["comment"] == "Verified the invoice total."


def test_review_over_threshold_requires_approval(
    client: TestClient,
    db_session: Session,
) -> None:
    """A corrected total over 20,000 still needs approval."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email="review-api-threshold@example.com",
        role=UserRole.MANAGER,
    )

    response = client.post(
        f"/workflows/{workflow.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "outcome": "resolved",
            "comment": "Confirmed the corrected total.",
            "corrected_total_amount": 25000,
        },
    )

    assert response.status_code == 200
    assert response.json()["workflow"]["current_status"] == "pending_approval"


def test_employee_cannot_submit_manual_review(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees cannot submit manager review decisions."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email="review-api-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    response = client.post(
        f"/workflows/{workflow.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "outcome": "resolved",
            "comment": "Employee should not be allowed.",
            "corrected_total_amount": 5000,
        },
    )

    assert response.status_code == 403

    db_session.refresh(workflow)
    assert workflow.current_status == WorkflowStatus.NEEDS_REVIEW


def test_manual_review_requires_authentication(
    client: TestClient,
) -> None:
    """Unauthenticated review requests are rejected."""

    response = client.post(
        "/workflows/999999/review",
        json={
            "outcome": "rejected",
            "comment": "Not authenticated.",
        },
    )

    assert response.status_code == 401


def test_manual_review_unknown_workflow_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    """An authenticated manager gets 404 for a missing workflow."""

    _, token = create_test_user_and_token(
        client,
        db_session,
        name="Review Missing Workflow Manager",
        email="review-api-missing@example.com",
        role=UserRole.MANAGER,
    )

    response = client.post(
        "/workflows/999999/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "outcome": "rejected",
            "comment": "Invalid workflow identifier.",
        },
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("outcome", "expected_status"),
    [
        ("rejected", "rejected"),
        ("information_requested", "needs_information"),
    ],
)
def test_manual_review_other_outcomes(
    client: TestClient,
    db_session: Session,
    outcome: str,
    expected_status: str,
) -> None:
    """Rejection and information requests update workflow status."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email=f"review-api-{outcome}@example.com",
        role=UserRole.MANAGER,
    )

    response = client.post(
        f"/workflows/{workflow.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "outcome": outcome,
            "comment": "Manager reviewed the document.",
        },
    )

    assert response.status_code == 200
    assert response.json()["workflow"]["current_status"] == expected_status

    if outcome == "information_requested":
        # Reload records after the API transaction commits.
        db_session.expire_all()

        information_request = (
            db_session.query(WorkflowInformationRequest)
            .filter(WorkflowInformationRequest.workflow_id == workflow.id)
            .one()
        )

        assert information_request.approval_id is None
        assert information_request.review_id == response.json()["review"]["id"]

        assert information_request.request_comment == ("Manager reviewed the document.")

        assert information_request.return_status == "needs_review"
        assert information_request.responded_at is None


@pytest.mark.parametrize(
    "payload",
    [
        {
            "outcome": "resolved",
            "comment": "Verified the invoice.",
        },
        {
            "outcome": "resolved",
            "comment": "   ",
            "corrected_total_amount": 5000,
        },
        {
            "outcome": "resolved",
            "comment": "Verified the invoice.",
            "corrected_total_amount": -100,
        },
        {
            "outcome": "invalid_outcome",
            "comment": "Invalid review outcome.",
        },
    ],
)
def test_invalid_manual_review_returns_422(
    client: TestClient,
    db_session: Session,
    payload: dict,
) -> None:
    """Invalid review requests must not change workflow state."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email="review-api-validation@example.com",
        role=UserRole.MANAGER,
    )

    response = client.post(
        f"/workflows/{workflow.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422

    db_session.refresh(workflow)
    assert workflow.current_status == WorkflowStatus.NEEDS_REVIEW


def test_duplicate_manual_review_returns_409(
    client: TestClient,
    db_session: Session,
) -> None:
    """A workflow cannot be reviewed again after resolution."""

    workflow, token = create_test_manual_review_workflow(
        client,
        db_session,
        email="review-api-duplicate@example.com",
        role=UserRole.MANAGER,
    )

    url = f"/workflows/{workflow.id}/review"
    headers = {"Authorization": f"Bearer {token}"}

    first_response = client.post(
        url,
        headers=headers,
        json={
            "outcome": "resolved",
            "comment": "Invoice verified.",
            "corrected_total_amount": 5000,
        },
    )

    assert first_response.status_code == 200

    # Check the status returned after the first review.
    print("FIRST RESPONSE:", first_response.json())

    # Reload the workflow from the database.
    db_session.expire_all()

    updated_workflow = get_workflow_by_id(
        database_session=db_session,
        workflow_id=workflow.id,
    )

    print(
        "DATABASE WORKFLOW STATUS:",
        updated_workflow.current_status,
    )

    second_response = client.post(
        url,
        headers=headers,
        json={
            "outcome": "rejected",
            "comment": "Attempting another decision.",
        },
    )

    assert second_response.status_code == 409

    db_session.refresh(workflow)

    assert workflow.current_status == WorkflowStatus.COMPLETED


# ---------------------------------------------------------
# Phase 12.5B - Employee information response API tests
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("initial_status", "endpoint", "decision_payload", "expected_status"),
    [
        (
            WorkflowStatus.PENDING_APPROVAL,
            "decision",
            {
                "decision": "information_requested",
                "comment": "Please provide the purchase order number.",
            },
            WorkflowStatus.PENDING_APPROVAL,
        ),
        (
            WorkflowStatus.NEEDS_REVIEW,
            "review",
            {
                "outcome": "information_requested",
                "comment": "Please clarify the invoice details.",
            },
            WorkflowStatus.NEEDS_REVIEW,
        ),
    ],
)
def test_employee_response_returns_to_correct_review_queue(
    client: TestClient,
    db_session: Session,
    initial_status: WorkflowStatus,
    endpoint: str,
    decision_payload: dict,
    expected_status: WorkflowStatus,
) -> None:
    """An employee response returns the workflow to its original queue."""

    owner, owner_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Response Employee",
        email=f"response-owner-{endpoint}@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Response Manager",
        email=f"response-manager-{endpoint}@example.com",
        role=UserRole.MANAGER,
    )

    document = create_test_document(
        db_session,
        uploaded_by=owner.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=initial_status,
    )

    # Manager requests information.
    manager_response = client.post(
        f"/workflows/{workflow.id}/{endpoint}",
        headers={"Authorization": f"Bearer {manager_token}"},
        json=decision_payload,
    )

    assert manager_response.status_code == 200
    assert manager_response.json()["workflow"]["current_status"] == (
        "needs_information"
    )

    # Employee answers the outstanding request.
    response = client.post(
        f"/workflows/{workflow.id}/information-response",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "response_comment": "Purchase order number: PO-2026-015.",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["workflow"]["current_status"] == expected_status.value

    assert response_data["information_request"]["response_comment"] == (
        "Purchase order number: PO-2026-015."
    )

    assert response_data["information_request"]["responded_by"] == owner.id
    assert response_data["information_request"]["responded_at"] is not None

    # Verify that PostgreSQL stores the response.
    db_session.expire_all()

    information_request = (
        db_session.query(WorkflowInformationRequest)
        .filter(WorkflowInformationRequest.workflow_id == workflow.id)
        .one()
    )

    assert information_request.responded_by == owner.id
    assert information_request.responded_at is not None
    assert information_request.return_status == expected_status.value


def test_other_employee_cannot_respond_to_information_request(
    client: TestClient,
    db_session: Session,
) -> None:
    """Employees cannot respond to requests for other people's documents."""

    owner, _ = create_test_user_and_token(
        client,
        db_session,
        name="Response Owner",
        email="response-owner-security@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, other_token = create_test_user_and_token(
        client,
        db_session,
        name="Unauthorized Employee",
        email="response-other-employee@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Response Security Manager",
        email="response-security-manager@example.com",
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

    manager_response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "decision": "information_requested",
            "comment": "Provide additional documentation.",
        },
    )

    assert manager_response.status_code == 200

    response = client.post(
        f"/workflows/{workflow.id}/information-response",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "response_comment": "Unauthorized response.",
        },
    )

    assert response.status_code == 403

    db_session.expire_all()

    persisted_workflow = db_session.get(Workflow, workflow.id)
    assert persisted_workflow is not None
    assert persisted_workflow.current_status == WorkflowStatus.NEEDS_INFORMATION

    information_request = (
        db_session.query(WorkflowInformationRequest)
        .filter(WorkflowInformationRequest.workflow_id == workflow.id)
        .one()
    )

    assert information_request.responded_at is None


def test_employee_cannot_respond_twice(
    client: TestClient,
    db_session: Session,
) -> None:
    """An information request can be answered only once."""

    owner, owner_token = create_test_user_and_token(
        client,
        db_session,
        name="Duplicate Response Employee",
        email="duplicate-response-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    _, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Duplicate Response Manager",
        email="duplicate-response-manager@example.com",
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

    manager_response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "decision": "information_requested",
            "comment": "Please verify the invoice.",
        },
    )

    assert manager_response.status_code == 200

    url = f"/workflows/{workflow.id}/information-response"
    headers = {"Authorization": f"Bearer {owner_token}"}

    first_response = client.post(
        url,
        headers=headers,
        json={
            "response_comment": "Invoice verified.",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        url,
        headers=headers,
        json={
            "response_comment": "Another response.",
        },
    )

    assert second_response.status_code == 409


def test_manager_list_excludes_unauthorized_workflows(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers see their assigned work and eligible shared work."""

    employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Filtering Document Owner",
        email="filtering-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    manager, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Filtering Manager",
        email="filtering-manager@example.com",
        role=UserRole.MANAGER,
    )

    other_manager, _ = create_test_user_and_token(
        client,
        db_session,
        name="Filtering Other Manager",
        email="filtering-other-manager@example.com",
        role=UserRole.MANAGER,
    )

    # 1. Workflow assigned to the logged-in manager.
    own_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )
    own_workflow = create_test_workflow(
        db_session,
        document_id=own_document.id,
    )
    own_workflow.assigned_to = manager.id

    # 2. Workflow assigned to another manager.
    other_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )
    other_workflow = create_test_workflow(
        db_session,
        document_id=other_document.id,
    )
    other_workflow.assigned_to = other_manager.id

    # 3. Unassigned workflow awaiting manager review.
    shared_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )
    shared_workflow = create_test_workflow(
        db_session,
        document_id=shared_document.id,
        status=WorkflowStatus.NEEDS_REVIEW,
    )

    # 4. Unassigned completed workflow.
    completed_document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )
    completed_workflow = create_test_workflow(
        db_session,
        document_id=completed_document.id,
        status=WorkflowStatus.COMPLETED,
    )

    db_session.commit()

    # Request the manager's workflow list.
    response = client.get(
        "/workflows",
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 200

    workflow_ids = {item["id"] for item in response.json()}

    # Manager can see assigned and eligible shared work.
    assert own_workflow.id in workflow_ids
    assert shared_workflow.id in workflow_ids

    # Manager cannot see unrelated restricted work.
    assert other_workflow.id not in workflow_ids
    assert completed_workflow.id not in workflow_ids


def test_other_manager_cannot_view_information_request(
    client: TestClient,
    db_session: Session,
) -> None:
    """Managers cannot view requests for another manager's workflow."""

    # Create the employee who owns the document.
    employee, _ = create_test_user_and_token(
        client,
        db_session,
        name="Information Access Owner",
        email="information-access-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    # Create the manager responsible for the workflow.
    assigned_manager, assigned_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Access Manager",
        email="information-access-manager@example.com",
        role=UserRole.MANAGER,
    )

    # Create another manager who should not have access.
    other_manager, other_token = create_test_user_and_token(
        client,
        db_session,
        name="Unauthorized Information Manager",
        email="unauthorized-information-manager@example.com",
        role=UserRole.MANAGER,
    )

    # Create a workflow awaiting manager approval.
    document = create_test_document(
        db_session,
        uploaded_by=employee.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    # Assign the workflow to the first manager.
    workflow.assigned_to = assigned_manager.id
    db_session.commit()

    # The assigned manager requests information.
    decision_response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={"Authorization": f"Bearer {assigned_token}"},
        json={
            "decision": "information_requested",
            "comment": "Please provide the purchase order.",
        },
    )

    assert decision_response.status_code == 200

    # Another manager attempts to read the request.
    response = client.get(
        f"/workflows/{workflow.id}/information-request",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert other_manager.id != assigned_manager.id
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You are not allowed to view this information request."
    )

    # Confirm the workflow is still waiting for information.
    db_session.refresh(workflow)
    assert workflow.current_status == WorkflowStatus.NEEDS_INFORMATION


@pytest.mark.parametrize(
    ("viewer", "expected_status"),
    [
        ("owner", 200),
        ("assigned_manager", 200),
        ("other_employee", 403),
    ],
)
def test_information_request_visibility_by_role(
    client: TestClient,
    db_session: Session,
    viewer: str,
    expected_status: int,
) -> None:
    """Only authorized users can view workflow information requests."""

    # Create the document owner.
    owner, owner_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Visibility Owner",
        email="info-visibility-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    # Create the manager responsible for reviewing the workflow.
    manager, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Information Visibility Manager",
        email="info-visibility-manager@example.com",
        role=UserRole.MANAGER,
    )

    # Create an unrelated employee.
    _, other_token = create_test_user_and_token(
        client,
        db_session,
        name="Other Information Visibility Employee",
        email="info-visibility-other@example.com",
        role=UserRole.EMPLOYEE,
    )

    # Create a document and its workflow.
    document = create_test_document(
        db_session,
        uploaded_by=owner.id,
    )

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=WorkflowStatus.PENDING_APPROVAL,
    )

    workflow.assigned_to = manager.id
    db_session.commit()

    # The assigned manager requests more information.
    decision_response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "decision": "information_requested",
            "comment": "Please provide the supporting invoice.",
        },
    )

    assert decision_response.status_code == 200

    # Choose which authenticated user will read the request.
    tokens = {
        "owner": owner_token,
        "assigned_manager": manager_token,
        "other_employee": other_token,
    }

    # Attempt to retrieve the open information request.
    response = client.get(
        f"/workflows/{workflow.id}/information-request",
        headers={
            "Authorization": f"Bearer {tokens[viewer]}",
        },
    )

    assert response.status_code == expected_status

    if expected_status == 200:
        # Authorized users can read the request comment.
        data = response.json()

        assert data["workflow_id"] == workflow.id
        assert data["request_comment"] == ("Please provide the supporting invoice.")

    else:
        # Unauthorized users must not see the request.
        assert response.json()["detail"] == (
            "You are not allowed to view this information request."
        )


def test_workflow_history_contains_review_and_approval(
    client: TestClient,
    db_session: Session,
) -> None:
    """History includes the correct manual-review and approval records."""

    # Create an authorized manager.
    manager, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="History Manager",
        email="history-manager@example.com",
        role=UserRole.MANAGER,
    )

    # Create a document belonging to the manager.
    document = create_test_document(
        db_session,
        uploaded_by=manager.id,
    )

    # Start with an invoice requiring manual review.
    document.extracted_data = {
        "invoice_number": "INV-HISTORY-001",
        "total_amount": None,
    }
    db_session.commit()

    workflow = create_test_workflow(
        db_session,
        document_id=document.id,
        status=WorkflowStatus.NEEDS_REVIEW,
    )

    # Keep the workflow visible after its status changes.
    workflow.assigned_to = manager.id
    db_session.commit()

    headers = {
        "Authorization": f"Bearer {manager_token}",
    }

    # Resolve the manual review with an amount requiring approval.
    review_response = client.post(
        f"/workflows/{workflow.id}/review",
        headers=headers,
        json={
            "outcome": "resolved",
            "comment": "Invoice total verified.",
            "corrected_total_amount": 25000,
        },
    )

    assert review_response.status_code == 200
    assert review_response.json()["workflow"]["current_status"] == "pending_approval"

    # Approve the corrected invoice.
    approval_response = client.post(
        f"/workflows/{workflow.id}/decision",
        headers=headers,
        json={
            "decision": "approved",
            "comment": "Approved after manual review.",
        },
    )

    assert approval_response.status_code == 200
    assert approval_response.json()["workflow"]["current_status"] == "approved"

    # Retrieve the workflow's decision history.
    response = client.get(
        f"/workflows/{workflow.id}/history",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    # Verify that the correct workflow and both records are returned.
    assert data["workflow_id"] == workflow.id
    assert len(data["history"]) == 2

    # Find records by action type rather than list position.
    history_by_type = {item["action_type"]: item for item in data["history"]}

    # Both decision types must exist.
    assert set(history_by_type) == {
        "manual_review",
        "approval",
    }

    # Verify the manual-review record.
    review = history_by_type["manual_review"]

    assert review["decision"] == "resolved"
    assert review["decided_by"] == manager.id
    assert review["comment"] == "Invoice total verified."
    assert review["created_at"] is not None
    assert isinstance(review["id"], int)

    # Verify the approval record.
    approval = history_by_type["approval"]

    assert approval["decision"] == "approved"
    assert approval["decided_by"] == manager.id
    assert approval["comment"] == "Approved after manual review."
    assert approval["created_at"] is not None
    assert isinstance(approval["id"], int)

    # Both records must contain valid timestamps.
    assert all(item["created_at"] for item in data["history"])


@pytest.mark.parametrize(
    ("viewer", "expected_status"),
    [
        ("owner", 200),
        ("assigned_manager", 200),
        ("other_manager", 403),
        ("admin", 200),
    ],
)
def test_workflow_history_visibility(
    client: TestClient,
    db_session: Session,
    viewer: str,
    expected_status: int,
) -> None:
    """Only authorized users can retrieve workflow decision history."""

    owner, owner_token = create_test_user_and_token(
        client,
        db_session,
        name="History Document Owner",
        email="history-visibility-owner@example.com",
        role=UserRole.EMPLOYEE,
    )

    manager, manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Assigned History Manager",
        email="history-visibility-manager@example.com",
        role=UserRole.MANAGER,
    )

    _, other_manager_token = create_test_user_and_token(
        client,
        db_session,
        name="Other History Manager",
        email="history-visibility-other-manager@example.com",
        role=UserRole.MANAGER,
    )

    _, admin_token = create_test_user_and_token(
        client,
        db_session,
        name="History Admin",
        email="history-visibility-admin@example.com",
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

    # Assign the workflow to one manager.
    workflow.assigned_to = manager.id
    db_session.commit()

    tokens = {
        "owner": owner_token,
        "assigned_manager": manager_token,
        "other_manager": other_manager_token,
        "admin": admin_token,
    }

    response = client.get(
        f"/workflows/{workflow.id}/history",
        headers={
            "Authorization": f"Bearer {tokens[viewer]}",
        },
    )

    assert response.status_code == expected_status

    if expected_status == 200:
        data = response.json()

        assert data["workflow_id"] == workflow.id
        assert data["history"] == []

    else:
        assert response.json()["detail"] == (
            "You are not allowed to view this workflow history."
        )
