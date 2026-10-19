from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.enums import DocumentType, UserRole
from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.db.models.user import User
from app.schemas.ai_schema import (
    DocumentClassification,
    InvoiceExtraction,
)


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
    assert response_data["is_indexed"] is False

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


def test_process_document_success(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An authenticated user can process their uploaded document."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="processor@example.com",
    )

    upload_response = client.post(
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

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert process_response.status_code == 200

    response_data = process_response.json()

    assert response_data["id"] == document_id
    assert response_data["status"] == "text_extracted"

    document = db_session.query(Document).filter(Document.id == document_id).one()

    db_session.refresh(document)

    assert document.status.value == "text_extracted"
    assert response_data["is_indexed"] is False
    assert document.extracted_text == "Employees must follow company policy."


def test_process_document_requires_authentication(
    client: TestClient,
) -> None:
    """Anonymous users cannot process documents."""

    response = client.post(
        "/documents/1/process",
    )

    assert response.status_code in (401, 403)


def test_process_document_returns_not_found(
    client: TestClient,
) -> None:
    """Processing an unknown document should return 404."""

    access_token = register_and_login(
        client,
        email="not-found@example.com",
    )

    response = client.post(
        "/documents/999999/process",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_process_document_rejects_different_user(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user cannot process a document uploaded by another user."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="document-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "private-document.txt",
                b"Private document content.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    other_user_token = register_and_login(
        client,
        email="different-user@example.com",
    )

    response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You are not allowed to process this document."
    )


def test_analyze_invoice_persists_business_rule_result(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    An analyzed invoice should persist its AI result and
    deterministic business-rule decision.
    """

    # Keep uploaded test files out of the real uploads directory.
    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="invoice-analysis@example.com",
    )

    # Step 1:
    # Upload a real TXT invoice through the HTTP API.
    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "invoice.txt",
                (
                    b"Invoice Number: INV-001\n"
                    b"Supplier: ABC Corporation\n"
                    b"Currency: PHP\n"
                    b"Total Amount: 25000.00\n"
                ),
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    # Step 2:
    # Run the real document-processing endpoint.
    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert process_response.status_code == 200
    assert process_response.json()["status"] == "text_extracted"

    # Step 3:
    # Prevent creation of a real OpenAI client.
    monkeypatch.setattr(
        "app.api.routes.document_routes.create_openai_client",
        lambda: Mock(),
    )

    # Mock only the AI classification boundary.
    monkeypatch.setattr(
        "app.ai.classifier.DocumentClassifier.classify",
        lambda self, document_text: DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.98,
        ),
    )

    # Mock only the AI extraction boundary.
    monkeypatch.setattr(
        "app.ai.extractor.InvoiceExtractor.extract",
        lambda self, document_text: InvoiceExtraction(
            invoice_number="INV-001",
            supplier="ABC Corporation",
            currency="PHP",
            total_amount=25000.00,
        ),
    )

    # Step 4:
    # Call the real analyze HTTP endpoint.
    analyze_response = client.post(
        f"/documents/{document_id}/analyze",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert analyze_response.status_code == 200

    response_data = analyze_response.json()

    assert response_data["id"] == document_id
    assert response_data["document_type"] == "invoice"
    assert response_data["status"] == "analyzed"
    assert response_data["is_indexed"] is False

    # Step 5:
    # Reload the document from PostgreSQL.
    db_session.expire_all()

    document = db_session.query(Document).filter(Document.id == document_id).one()

    # Verify Phase 7 persistence.
    assert document.document_type == DocumentType.INVOICE
    assert document.classification_confidence == 0.98
    assert document.status.value == "analyzed"

    assert document.extracted_data is not None
    assert document.extracted_data["invoice_number"] == "INV-001"
    assert document.extracted_data["supplier"] == "ABC Corporation"
    assert document.extracted_data["currency"] == "PHP"
    assert document.extracted_data["total_amount"] == 25000.00

    # Verify Phase 8 persistence.
    assert document.business_rule_result is not None

    assert document.business_rule_result["requires_approval"] is True
    assert document.business_rule_result["approval_role"] == "manager"
    assert document.business_rule_result["requires_manual_review"] is False
    assert document.business_rule_result["next_action"] == "manager_review"
    assert (
        document.business_rule_result["reason"]
        == "Invoice total exceeds the manager approval threshold."
    )


def test_index_document_success(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A processed document can be indexed for RAG retrieval."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="rag-index@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "policy.txt",
                (
                    b"Employees receive 15 days of annual leave per year. "
                    b"Unused annual leave may be carried forward."
                ),
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert process_response.status_code == 200
    assert process_response.json()["status"] == "text_extracted"

    monkeypatch.setattr(
        "app.ai.embedder.DocumentEmbedder.embed_texts",
        lambda self, texts: [[0.1] * 1536 for _ in texts],
    )

    index_response = client.post(
        f"/documents/{document_id}/index",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert index_response.status_code == 200

    response_data = index_response.json()

    assert response_data["document_id"] == document_id
    assert response_data["chunks_indexed"] >= 1

    chunks = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    assert len(chunks) == response_data["chunks_indexed"]

    assert all(chunk.embedding is not None for chunk in chunks)

    db_session.expire_all()

    document = db_session.query(Document).filter(Document.id == document_id).one()

    assert document.is_indexed is True


def test_index_document_requires_authentication(
    client: TestClient,
) -> None:
    """Anonymous users cannot index documents."""

    response = client.post(
        "/documents/1/index",
    )

    assert response.status_code in (401, 403)


def test_index_document_returns_not_found(
    client: TestClient,
) -> None:
    """Indexing an unknown document should return 404."""

    access_token = register_and_login(
        client,
        email="rag-index-not-found@example.com",
    )

    response = client.post(
        "/documents/999999/index",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_index_document_rejects_different_user(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user cannot index a document uploaded by another user."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="rag-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "private-policy.txt",
                b"Confidential company policy.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    other_user_token = register_and_login(
        client,
        email="rag-other-user@example.com",
    )

    response = client.post(
        f"/documents/{document_id}/index",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("You are not allowed to index this document.")


def test_ask_document_question_success(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An authenticated user can ask a question about an indexed document."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="rag-question@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "leave-policy.txt",
                (
                    b"Employees receive 15 days of annual leave per year. "
                    b"Unused leave may be carried forward."
                ),
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert process_response.status_code == 200

    monkeypatch.setattr(
        "app.ai.embedder.DocumentEmbedder.embed_texts",
        lambda self, texts: [[0.1] * 1536 for _ in texts],
    )

    index_response = client.post(
        f"/documents/{document_id}/index",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert index_response.status_code == 200

    monkeypatch.setattr(
        "app.ai.qa_generator.DocumentQAGenerator.generate",
        lambda self, question, context: "Employees receive 15 days of annual leave.",
    )

    ask_response = client.post(
        f"/documents/{document_id}/ask",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "question": "How many annual leave days do employees receive?",
        },
    )

    assert ask_response.status_code == 200

    response_data = ask_response.json()

    assert response_data["answer"] == ("Employees receive 15 days of annual leave.")

    assert "sources" in response_data
    assert len(response_data["sources"]) >= 1

    assert "chunk_index" in response_data["sources"][0]
    assert "content" in response_data["sources"][0]


def test_ask_document_question_requires_authentication(
    client: TestClient,
) -> None:
    """Anonymous users cannot ask questions about documents."""

    response = client.post(
        "/documents/1/ask",
        json={
            "question": "What is this document about?",
        },
    )

    assert response.status_code in (401, 403)


def test_ask_document_question_returns_not_found(
    client: TestClient,
) -> None:
    """Asking about an unknown document should return 404."""

    access_token = register_and_login(
        client,
        email="rag-question-not-found@example.com",
    )

    response = client.post(
        "/documents/999999/ask",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "question": "What is this document about?",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_ask_document_question_rejects_different_user(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user cannot ask questions about another user's document."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="rag-question-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "private-policy.txt",
                b"Private company policy.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    other_user_token = register_and_login(
        client,
        email="rag-question-other@example.com",
    )

    response = client.post(
        f"/documents/{document_id}/ask",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
        json={
            "question": "What does this document say?",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You are not allowed to ask questions about this document."
    )


def test_document_owner_can_view_document_details(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The document owner should be able to view detailed document data."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    access_token = register_and_login(
        client,
        email="document-detail-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "uploaded_file": (
                "review-document.txt",
                b"Invoice Number: INV-DETAIL-001",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    document = db_session.get(
        Document,
        document_id,
    )

    assert document is not None

    document.extracted_text = "Invoice Number: INV-DETAIL-001"
    document.summary = "Invoice requiring manager review."
    document.document_type = DocumentType.INVOICE
    document.classification_confidence = 0.97
    document.extracted_data = {
        "invoice_number": "INV-DETAIL-001",
        "total_amount": 25000.00,
    }
    document.business_rule_result = {
        "requires_approval": True,
        "approval_role": "manager",
        "next_action": "manager_review",
    }

    db_session.commit()

    response = client.get(
        f"/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == document_id
    assert response_data["original_file_name"] == "review-document.txt"
    assert response_data["document_type"] == "invoice"
    assert response_data["extracted_text"] == ("Invoice Number: INV-DETAIL-001")
    assert response_data["summary"] == ("Invoice requiring manager review.")
    assert response_data["classification_confidence"] == 0.97

    assert response_data["extracted_data"] == {
        "invoice_number": "INV-DETAIL-001",
        "total_amount": 25000.00,
    }

    assert response_data["business_rule_result"] == {
        "requires_approval": True,
        "approval_role": "manager",
        "next_action": "manager_review",
    }

    # Internal storage information must stay private.
    assert "stored_file_name" not in response_data
    assert "file_path" not in response_data


def test_employee_cannot_view_another_users_document_details(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Employees should not view another user's document details."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="detail-document-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "private-review.txt",
                b"Private review document.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    other_employee_token = register_and_login(
        client,
        email="detail-other-employee@example.com",
    )

    response = client.get(
        f"/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {other_employee_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("You are not allowed to view this document.")


def test_manager_can_view_another_users_document_details(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Managers should be able to review employee documents."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="manager-review-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "manager-review.txt",
                b"Document for manager review.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    manager_email = "document-review-manager@example.com"

    manager_token = register_and_login(
        client,
        email=manager_email,
    )

    manager = db_session.query(User).filter(User.email == manager_email).one()

    manager.role = UserRole.MANAGER
    db_session.commit()
    db_session.refresh(manager)

    response = client.get(
        f"/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == document_id


def test_admin_can_view_another_users_document_details(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admins should be able to review employee documents."""

    monkeypatch.setattr(
        "app.storage.file_storage.UPLOAD_DIRECTORY",
        tmp_path,
    )

    owner_token = register_and_login(
        client,
        email="admin-review-owner@example.com",
    )

    upload_response = client.post(
        "/documents",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        files={
            "uploaded_file": (
                "admin-review.txt",
                b"Document for admin review.",
                "text/plain",
            ),
        },
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    admin_email = "document-review-admin@example.com"

    admin_token = register_and_login(
        client,
        email=admin_email,
    )

    admin = db_session.query(User).filter(User.email == admin_email).one()

    admin.role = UserRole.ADMIN
    db_session.commit()
    db_session.refresh(admin)

    response = client.get(
        f"/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == document_id


def test_get_document_details_returns_not_found(
    client: TestClient,
) -> None:
    """Unknown document IDs should return 404."""

    access_token = register_and_login(
        client,
        email="document-detail-not-found@example.com",
    )

    response = client.get(
        "/documents/999999",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_get_document_details_requires_authentication(
    client: TestClient,
) -> None:
    """Anonymous users should not be able to view document details."""

    response = client.get(
        "/documents/1",
    )

    assert response.status_code in (401, 403)
