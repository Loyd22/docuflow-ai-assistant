````markdown
# DocuFlow AI

DocuFlow AI is an AI-powered document-processing and workflow automation system designed to automate business document intake, classification, extraction, routing, approval, and retrieval.

The project is being built incrementally using a modular monolith architecture with clear separation between API routes, schemas, services, repositories, database models, security, file storage, AI logic, and tests.

---

## Current Project Status

Completed:

* Phase 1 — Project Setup
* Phase 2 — Backend Foundation
* Phase 3 — Database Design
* Phase 4 — Authentication & Authorization
* Phase 5 — Document Upload

Next:

* Phase 6 — Document Processing

---

## Technology Stack

### Frontend

* React
* Vite
* TypeScript

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

### Database

* PostgreSQL 16
* Psycopg

### Authentication & Security

* JWT authentication
* PyJWT
* Argon2 password hashing through `pwdlib`
* Role-based authorization

### File Upload & Storage

* FastAPI `UploadFile`
* `multipart/form-data`
* Local filesystem storage
* UUID-based stored filenames

### Infrastructure & Development

* Docker
* Docker Compose
* pytest
* FastAPI TestClient
* Ruff

---

## Project Architecture

DocuFlow currently follows a modular monolith structure.

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth_routes.py
│   │   │   ├── document_routes.py
│   │   │   └── health_routes.py
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── workflow.py
│   │   │   ├── approval.py
│   │   │   └── audit_log.py
│   │   ├── base.py
│   │   ├── database.py
│   │   ├── enums.py
│   │   └── session.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── document_repository.py
│   │
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   └── document_schema.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   └── document_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_storage.py
│   │
│   └── main.py
│
├── migrations/
│
├── tests/
│   ├── conftest.py
│   ├── test_auth_api.py
│   ├── test_auth_service.py
│   ├── test_document_api.py
│   ├── test_document_service.py
│   └── test_health.py
│
├── uploads/
├── alembic.ini
├── requirements.txt
├── .env
└── .env.example
````

The application follows this general request flow:

```text
HTTP Request
↓
Pydantic Schema / FastAPI Input
↓
API Route
↓
Service
↓
Repository
↓
SQLAlchemy
↓
PostgreSQL
```

Document uploads also use a dedicated file-storage layer:

```text
HTTP Upload
↓
Document Route
↓
Document Service
├── File Storage
│   ↓
│   backend/uploads/
│
└── Document Repository
    ↓
    PostgreSQL
```

Security-specific functionality is kept inside the core security layer.

---

## Database Models

The initial database schema contains:

* `users`
* `documents`
* `workflows`
* `approvals`
* `audit_logs`

Database schema changes are managed through Alembic migrations.

Do not use `Base.metadata.create_all()` as the normal development or production migration strategy.

The automated test environment may use `Base.metadata.create_all()` and `Base.metadata.drop_all()` to create and destroy an isolated disposable test schema.

---

## Authentication & Authorization

Phase 4 introduced JWT-based authentication and role-based authorization.

### Authentication Endpoints

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Registration

New users provide:

```json
{
  "name": "Test Employee",
  "email": "test@example.com",
  "password": "password123"
}
```

Passwords are never stored directly.

The registration flow is:

```text
Request
↓
Validate input
↓
Normalize email
↓
Check duplicate account
↓
Hash password using Argon2
↓
Store password_hash
↓
Create User
```

New accounts default to:

```text
employee
```

Users cannot assign themselves elevated roles during registration.

### Login

Login accepts:

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

Successful authentication returns:

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

Protected requests use:

```text
Authorization: Bearer <access_token>
```

### Current User

```text
GET /auth/me
```

validates the JWT, resolves the current user from PostgreSQL, verifies that the account is active, and returns safe user information.

### Roles

DocuFlow currently supports:

```text
employee
manager
admin
```

These roles are represented using the `UserRole` enum.

Authorization is enforced by the backend through reusable FastAPI dependencies.

```text
Authentication
→ Who is this user?

Authorization
→ Is this user allowed to perform this action?
```

Inactive accounts are rejected without deleting historical business records.

---

## Document Upload

Phase 5 introduced authenticated document upload with file validation, local file storage, database metadata persistence, cleanup handling, and automated tests.

### Document Upload Endpoint

```text
POST /documents
```

The endpoint requires authentication using:

```text
Authorization: Bearer <access_token>
```

Anonymous users cannot upload documents.

### Supported File Types

The current upload implementation accepts:

```text
.pdf
.docx
.txt
```

Additional file types can be introduced later when document-processing requirements expand.

### Maximum File Size

The current maximum upload size is:

```text
10 MB
```

Empty files are rejected.

### Upload Flow

```text
Authenticated User
↓
POST /documents
↓
Resolve current user
↓
Validate filename
↓
Validate file extension
↓
Generate unique stored filename
↓
Save physical file
↓
Validate actual file size
↓
Create document metadata record
↓
Return safe document response
```

### File Storage

Uploaded files are currently stored locally in:

```text
backend/uploads/
```

The file-storage layer generates a unique internal filename using a UUID instead of storing files directly under the user's original filename.

Example:

```text
Original filename:
invoice.pdf

Stored filename:
7bb65f93b6b44266b3dba9fc31fd6c87.pdf
```

The original filename is preserved in PostgreSQL.

This helps prevent filename collisions when multiple users upload files with the same name.

For example:

```text
User A uploads:
invoice.pdf

User B uploads:
invoice.pdf
```

DocuFlow can safely store them as:

```text
a1f5d6...pdf
b8c9e2...pdf
```

while keeping each original filename in the database.

### Document Metadata

The `documents` table stores metadata and processing information including:

```text
id
uploaded_by
original_file_name
stored_file_name
file_path
mime_type
file_size
document_type
status
extracted_text
summary
created_at
updated_at
```

Newly uploaded documents currently default to:

```text
document_type = unknown
status = uploaded
```

The following fields are present for later processing phases:

```text
extracted_text
summary
```

They are not populated during Phase 5.

### Uploader Identity

The client does not provide the `uploaded_by` value directly.

Instead, the backend determines the uploader from the authenticated user.

```text
Authorization Header
↓
JWT
↓
get_current_user
↓
User
↓
current_user.id
↓
Document.uploaded_by
```

This prevents a client from claiming that another account uploaded the document.

For example, the client cannot safely override ownership using data such as:

```json
{
  "uploaded_by": 999
}
```

The backend remains the authority for the uploader identity.

### Public Document Response

The upload endpoint returns safe business-facing document information such as:

```text
id
uploaded_by
original_file_name
mime_type
file_size
document_type
status
created_at
updated_at
```

Internal file-storage details are intentionally not exposed:

```text
stored_file_name
file_path
```

This prevents the API from leaking backend filesystem implementation details.

### Upload Failure Cleanup

File storage and database persistence are separate operations.

A possible failure scenario is:

```text
Save physical file
↓
Try to create database record
↓
Database operation fails
```

Without cleanup, this could leave a file in:

```text
backend/uploads/
```

without a corresponding document record.

The document service therefore performs cleanup:

```text
Save file
↓
Create database record
↓
Database failure
↓
Delete saved file
↓
Rollback SQLAlchemy transaction
↓
Raise error
```

This helps prevent orphaned files.

### File Validation

The current Phase 5 upload layer validates:

* filename presence
* supported file extension
* empty files
* maximum file size

Unsupported extensions are rejected.

Example:

```text
.exe
```

results in a `400 Bad Request`.

The current implementation does not yet perform deep file-content or file-signature validation.

For example, a malicious user could theoretically rename a file:

```text
malware.exe
```

to:

```text
report.pdf
```

More advanced file validation may later include:

```text
filename extension
+
declared MIME type
+
actual file signature
```

That type of ingestion hardening can be added during later processing/security work.

---

## Local Development

### Requirements

Install:

* Python 3.12+
* Docker Desktop
* Node.js
* Git

---

## Start PostgreSQL

From the project directory:

```bash
docker compose up -d
```

PostgreSQL is exposed locally through:

```text
localhost:5434
```

The Docker container continues to use PostgreSQL's internal port:

```text
5432
```

Check running containers:

```bash
docker ps
```

---

## Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create:

```text
backend/.env
```

using `.env.example` as the reference.

Relevant configuration includes:

```env
APP_NAME=DocuFlow AI

APP_ENV=development

APP_DEBUG=true

POSTGRES_HOST=localhost

POSTGRES_PORT=5434

POSTGRES_DB=docuflow

POSTGRES_USER=your_postgres_user

POSTGRES_PASSWORD=your_postgres_password

JWT_SECRET_KEY=your_secure_random_secret

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5434/docuflow_test
```

Never commit real secrets from `.env`.

To generate a JWT secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Migrations

Alembic is used for schema migrations.

Create a migration:

```bash
alembic revision --autogenerate -m "migration description"
```

Apply migrations:

```bash
alembic upgrade head
```

Check the active migration:

```bash
alembic current
```

Development and production database schema changes should be handled through Alembic.

Do not replace Alembic with:

```python
Base.metadata.create_all()
```

for normal application database management.

---

## Run the Backend

From:

```text
backend/
```

run:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Health Checks

Application health:

```text
GET /health
```

Database health:

```text
GET /health/database
```

The database health endpoint verifies PostgreSQL connectivity using a simple lightweight SQL query.

---

## Testing

DocuFlow uses `pytest`.

Run the complete test suite:

```bash
pytest -v
```

The test suite is divided between service-level unit tests and API/database integration tests.

### Health Tests

Current health testing includes:

* application health endpoint

### Authentication Service Unit Tests

Current authentication service testing includes:

* successful registration
* email normalization
* password hashing
* duplicate email rejection
* successful login
* incorrect password rejection
* unknown email rejection
* inactive-user rejection

### Authentication API Integration Tests

Current authentication API integration testing includes:

* successful registration
* duplicate registration
* successful login
* incorrect password
* unknown email
* authenticated `/auth/me`
* missing authentication
* invalid JWT
* employee authorization
* manager authorization
* admin authorization

Phase 4 originally reached:

```text
18 passed
```

before temporary authorization verification endpoints were reviewed and the test suite continued evolving.

### Document Service Unit Tests

Phase 5 introduced service-level tests for:

* successful document upload
* unsupported file extension rejection
* empty-file rejection
* oversized-file rejection
* saved-file cleanup when database persistence fails

These tests isolate the document service from external infrastructure where appropriate using mocks.

The service tests verify business behavior such as:

```text
Document Service
↓
Validate input
↓
Coordinate file storage
↓
Coordinate repository call
↓
Handle failure cleanup
```

### Document API Integration Tests

Phase 5 also introduced API integration tests for:

* successful authenticated document upload
* authentication requirement
* unsupported extension rejection
* empty-file rejection
* database metadata persistence
* physical file persistence
* safe response fields

These tests exercise the real application layers together:

```text
HTTP Request
↓
FastAPI
↓
Authentication
↓
Document Route
↓
Document Service
↓
Document Repository
↓
SQLAlchemy
↓
PostgreSQL Test Database
```

The tests also exercise real filesystem operations using pytest temporary directories.

### Test Database

A separate PostgreSQL test database is used for integration testing:

```text
docuflow_test
```

This prevents automated tests from modifying the normal development database.

The test database configuration is provided through:

```text
TEST_DATABASE_URL
```

The test suite overrides the application's normal database dependency so API requests execute against the test database.

Test transactions are rolled back after tests where appropriate.

### Temporary File Storage During Tests

Document API tests do not write test files into the normal development upload folder.

Instead, pytest's:

```text
tmp_path
```

fixture is used.

The storage location is temporarily redirected during a test:

```text
normal application:
backend/uploads/

test:
temporary pytest directory
```

This prevents automated tests from leaving test documents in the real upload directory.

### Current Test Result

After Phase 5 implementation:

```text
28 passed
```

The current suite covers:

```text
Health
+
Authentication
+
Authorization
+
Document Service
+
Document Upload API
+
PostgreSQL Integration
+
Filesystem Integration
```

Known non-failing warnings currently include:

* a Starlette TestClient/httpx deprecation warning
* a SQLAlchemy transaction cleanup warning in one document integration test path

These warnings do not currently cause test failures but can be addressed during later test-maintenance work.

---

## Code Quality

DocuFlow uses Ruff for Python linting and formatting.

Run lint checks:

```bash
ruff check .
```

Automatically fix supported lint issues:

```bash
ruff check . --fix
```

Format the Python codebase:

```bash
ruff format .
```

Check formatting without modifying files:

```bash
ruff format --check .
```

After lint or formatting changes, rerun:

```bash
pytest -v
```

to verify that code-quality changes did not introduce regressions.

The development workflow is:

```text
Implement feature
↓
Run feature-specific tests
↓
Run full pytest suite
↓
Run Ruff lint checks
↓
Run Ruff formatting check
↓
Review
↓
Commit
```

---

## Planned Document Processing Pipeline

DocuFlow's workflow is:

```text
Document Upload
↓
Text Extraction
↓
AI Classification
↓
Structured Data Extraction
↓
Business Rule Validation
↓
Workflow Routing
↓
Approval
↓
RAG / Document Q&A
↓
Dashboard & Audit Logs
```

Phase 5 completed:

```text
Document Upload
```

The next major capability is:

```text
Text Extraction
```

which belongs to:

```text
Phase 6 — Document Processing
```

Phase 6 will take documents that are already safely uploaded and begin turning their file contents into text that later AI components can work with.

The conceptual flow will become:

```text
Uploaded Document
↓
Locate stored file
↓
Determine document format
↓
Extract text
↓
Store extracted text
↓
Update document processing status
```

AI classification is intentionally not part of Phase 6.

The processing pipeline remains separated:

```text
Phase 5
Upload

↓

Phase 6
Extract document content

↓

Phase 7
AI classification and structured extraction
```

---

## Planned Supported Document Types

DocuFlow is designed to support:

* Invoice
* SOP
* Contract
* HR Form
* Purchase Request
* Policy Document
* Business Report
* Support Ticket
* Digital Form
* Memo / Announcement

Examples:

```text
Invoice
→ payment or billing document

SOP
→ step-by-step company process

Contract
→ agreement between company and client/vendor

HR Form
→ employee-related request or form

Purchase Request
→ request to purchase something

Policy Document
→ company rules or policies

Business Report
→ company update or performance report

Support Ticket
→ request for assistance

Digital Form
→ online business-process form

Memo / Announcement
→ official internal company communication
```

During Phase 5, uploaded documents begin as:

```text
document_type = unknown
```

This is intentional.

The upload system should not guess the document type.

Later:

```text
Phase 7 — AI Classification & Extraction
```

will classify supported documents and update the `document_type` value.

---

## Development Phases

```text
Phase 1  — Project Setup
Phase 2  — Backend Foundation
Phase 3  — Database Design
Phase 4  — Authentication & Authorization
Phase 5  — Document Upload
Phase 6  — Document Processing
Phase 7  — AI Classification & Extraction
Phase 8  — Business Rules
Phase 9  — Workflow & Approval
Phase 10 — RAG / Document Q&A
Phase 11 — Dashboard & Audit Logs
Phase 12 — Frontend
Phase 13 — Testing
Phase 14 — Deployment / DevOps
```

Current status:

```text
Phase 1  — Completed
Phase 2  — Completed
Phase 3  — Completed
Phase 4  — Completed
Phase 5  — Completed

Phase 6  — Next
```

The project is developed incrementally, with each phase reviewed and tested before the next major feature is introduced.

Before moving to the next development phase:

```text
1. Run the complete test suite
2. Run code-quality checks
3. Review the completed architecture
4. Update this README
5. Commit the completed phase
6. Push the latest code to the remote Git repository
7. Begin the next phase
```

```

This version keeps the original README detail and adds the full Phase 5 implementation rather than replacing it with a shorter summary. 
```
