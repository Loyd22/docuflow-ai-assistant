# DocuFlow AI

DocuFlow AI is an AI-powered document-processing and workflow automation system designed to automate business document intake, classification, extraction, routing, approval, and retrieval.

The project is being built incrementally using a modular monolith architecture with clear separation between API routes, schemas, services, repositories, database models, security, file storage, document processing, AI logic, and tests.

---

## Current Project Status

Completed:

* Phase 1 — Project Setup
* Phase 2 — Backend Foundation
* Phase 3 — Database Design
* Phase 4 — Authentication & Authorization
* Phase 5 — Document Upload
* Phase 6 — Document Processing
* Phase 7 — AI Classification & Extraction

Next:

* Phase 8 — Business Rules

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

### File Handling

* FastAPI `UploadFile`
* Multipart form-data uploads
* Local filesystem storage
* UUID-based internal filenames

### Document Processing

* `python-docx` for DOCX text extraction
* `pypdf` for PDF text extraction
* Python `pathlib` and built-in text reading for TXT files
* Extractor factory for file-type selection
* Processing-status tracking
* Controlled processing exceptions

### AI Classification & Extraction

* OpenAI Python SDK
* OpenAI Responses API
* Configurable AI model through environment settings
* Structured outputs validated with Pydantic
* Document classification across supported DocuFlow document types
* Invoice-specific structured field extraction
* AI-specific application exceptions and controlled API responses
* Persistent AI-processing status tracking
* PostgreSQL JSONB storage for structured extracted data
* Separate AI evaluation suite for model-quality measurement

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
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   ├── prompts.py
│   │   └── exceptions.py
│   │
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
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── base_extractor.py
│   │   ├── text_extractor.py
│   │   ├── docx_extractor.py
│   │   ├── pdf_extractor.py
│   │   ├── extractor_factory.py
│   │   └── exceptions.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── document_repository.py
│   │
│   ├── schemas/
│   │   ├── ai_schema.py
│   │   ├── auth_schema.py
│   │   └── document_schema.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   ├── document_processing_service.py
│   │   ├── document_ai_service.py
│   │   └── document_analysis_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_storage.py
│   │
│   └── main.py
│
├── evals/
│   ├── __init__.py
│   ├── classification_cases.py
│   ├── invoice_extraction_cases.py
│   ├── run_classification_eval.py
│   └── run_invoice_extraction_eval.py
│
├── migrations/
│
├── tests/
│   ├── conftest.py
│   ├── test_auth_api.py
│   ├── test_auth_service.py
│   ├── test_document_api.py
│   ├── test_document_processing_service.py
│   ├── test_document_service.py
│   ├── test_document_classifier.py
│   ├── test_invoice_extractor.py
│   ├── test_document_ai_service.py
│   ├── test_document_analysis_service.py
│   ├── test_docx_extractor.py
│   ├── test_extractor_factory.py
│   ├── test_health.py
│   ├── test_pdf_extractor.py
│   └── test_text_extractor.py
│
├── uploads/
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── .env
└── .env.example
```

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

Document uploads use a dedicated storage layer:

```text
Document Service
↓
File Storage Layer
↓
Local Upload Directory
```

Document processing uses a dedicated processing layer:

```text
Document Processing Service
↓
Extractor Factory
↓
TXT / DOCX / PDF Extractor
↓
Extracted Text
↓
Document Repository
↓
PostgreSQL
```

AI analysis uses dedicated AI and orchestration layers:

```text
Extracted Text
↓
Document Analysis Service
↓
Document AI Service
↓
Document Classifier
↓
Invoice Extractor when document_type = invoice
↓
Validated Pydantic Structured Output
↓
Document Repository
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

The automated integration-test environment may use `create_all()` and `drop_all()` to create and remove an isolated disposable test schema.

The `documents` table stores metadata and processing results including:

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
classification_confidence
extracted_data
summary
created_at
updated_at
```

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

The endpoint validates the JWT, resolves the current user from PostgreSQL, verifies that the account is active, and returns safe user information.

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

Phase 5 introduced authenticated document uploads with validation, local file storage, metadata persistence, cleanup handling, and automated tests.

### Document Upload Endpoint

```text
POST /documents
```

The endpoint requires authentication:

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
Create document database record
↓
Return safe document metadata
```

### File Storage

Uploaded files are currently stored locally in:

```text
backend/uploads/
```

The storage layer generates a unique internal filename using a UUID rather than directly storing the file using its user-provided name.

Example:

```text
Original filename:
invoice.pdf

Stored filename:
7bb65f93b6b44266b3dba9fc31fd6c87.pdf
```

The original filename is still preserved in PostgreSQL.

### New Document State

New uploads default to:

```text
document_type = unknown
status = uploaded
```

### Uploader Identity

Clients do not provide `uploaded_by` themselves.

Instead:

```text
JWT
↓
get_current_user
↓
current_user.id
↓
Document.uploaded_by
```

This prevents users from claiming another account as the uploader.

### Public Document Response

The document API returns safe business-facing metadata such as:

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

Internal fields such as:

```text
stored_file_name
file_path
```

are not exposed through the public response.

### Upload Failure Cleanup

If the physical file is saved but database persistence fails:

```text
Save file
↓
Create database record
↓
Database failure
↓
Delete saved file
↓
Rollback transaction
↓
Propagate error
```

This helps prevent orphaned files.

### Upload Validation

Phase 5 validates:

* filename presence
* supported file extension
* empty files
* maximum file size

Deep file-signature validation is not yet implemented.

---

## Document Processing

Phase 6 introduced document text extraction for uploaded TXT, DOCX, and PDF files.

The goal is to transform stored files into machine-readable text for later AI analysis.

### Processing Endpoint

```text
POST /documents/{document_id}/process
```

The endpoint requires authentication.

Only the user who uploaded the document can currently trigger processing.

### Processing Flow

```text
Authenticated User
↓
POST /documents/{document_id}/process
↓
Find document in PostgreSQL
↓
Verify document ownership
↓
Set status = processing
↓
Document Processing Service
↓
Extractor Factory
↓
Choose TXT / DOCX / PDF extractor
↓
Extract text
↓
Store extracted_text
↓
Set status = text_extracted
↓
Persist document
↓
Return safe document metadata
```

### Extractor Architecture

All extractors follow:

```text
extract(file_path) -> str
```

Current hierarchy:

```text
BaseTextExtractor
├── TextExtractor
├── DOCXExtractor
└── PDFExtractor
```

The `ExtractorFactory` selects the extractor by file extension:

```text
.txt  → TextExtractor
.docx → DOCXExtractor
.pdf  → PDFExtractor
```

### TXT Extraction

TXT files are read using UTF-8 text reading.

### DOCX Extraction

DOCX files are processed using `python-docx`.

The extractor:

* opens the document
* reads paragraph text
* ignores empty paragraphs
* combines readable paragraphs

### PDF Extraction

PDF files are processed using `pypdf`.

The extractor:

* opens the PDF
* iterates through pages
* extracts machine-readable text
* ignores pages without usable text
* combines readable text

The current implementation supports text-based PDFs.

Scanned or image-only PDFs may require OCR in a future enhancement.

### Processing Status Lifecycle

Successful processing:

```text
uploaded
↓
processing
↓
text_extracted
```

Failed processing:

```text
uploaded
↓
processing
↓
processing_failed
```

### Empty Extraction Handling

If extraction returns only empty or whitespace content:

```text
Extraction result
↓
No usable text
↓
processing_failed
```

The service raises a controlled `DocumentProcessingError`.

### Processing Failure Handling

Examples include:

```text
missing file
corrupted document
unreadable document
unsupported extraction condition
empty extracted text
```

The service:

```text
detects error
↓
sets status = processing_failed
↓
persists failed state
↓
raises DocumentProcessingError
```

### Processing API Errors

```text
Document does not exist
→ 404 Not Found

Authenticated user does not own document
→ 403 Forbidden

Document cannot be processed
→ 400 Bad Request
```

---

## AI Classification & Extraction

Phase 7 introduced DocuFlow's first real LLM-powered document-analysis pipeline.

The AI layer takes machine-readable text produced by Phase 6, classifies the document, extracts supported structured business fields, validates the AI output, and persists the result.

### Analysis Endpoint

```text
POST /documents/{document_id}/analyze
```

The endpoint requires authentication.

Only the user who uploaded the document can currently trigger AI analysis.

The document must already have:

```text
status = text_extracted
```

before AI analysis begins.

### AI Analysis Flow

```text
Authenticated User
↓
POST /documents/{document_id}/analyze
↓
Find document in PostgreSQL
↓
Verify document ownership
↓
Verify status = text_extracted
↓
Set status = ai_processing
↓
Document Analysis Service
↓
Document AI Service
↓
Document Classifier
↓
Structured Extractor when supported
↓
Validate structured output with Pydantic
↓
Persist document_type
↓
Persist classification_confidence
↓
Persist extracted_data
↓
Set status = analyzed
↓
Return safe document metadata
```

If classification or extraction fails:

```text
text_extracted
↓
ai_processing
↓
AI failure
↓
ai_processing_failed
```

### AI Layer Architecture

```text
app/ai/
├── client.py
├── classifier.py
├── extractor.py
├── prompts.py
└── exceptions.py
```

Responsibilities:

```text
client.py
→ creates/configures the OpenAI SDK client

classifier.py
→ determines document type

extractor.py
→ extracts supported structured fields

prompts.py
→ stores LLM instructions separately from orchestration logic

exceptions.py
→ exposes controlled DocuFlow AI-domain errors

ai_schema.py
→ validates structured AI outputs using Pydantic

document_ai_service.py
→ orchestrates classification and structured extraction

document_analysis_service.py
→ coordinates document lifecycle, persistence, and AI analysis

document_repository.py
→ persists AI results and document statuses
```

Provider-specific logic is kept outside API routes and database repositories.

### Supported Classification Types

The classifier currently recognizes:

```text
invoice
contract
sop
hr_form
purchase_request
policy
business_report
support_ticket
digital_form
memo
unknown
```

`unknown` is intentionally supported so the model is not forced to assign an incorrect business type.

### Structured Invoice Extraction

Invoice extraction is the first implemented document-specific extraction workflow.

The validated invoice schema contains:

```text
invoice_number
supplier
invoice_date
due_date
currency
subtotal
tax
total_amount
```

Missing values are allowed to remain `null`.

The extraction prompt explicitly instructs the model not to invent missing business data.

Example:

```json
{
  "invoice_number": "INV-2026-001",
  "supplier": "ABC Office Supplies",
  "invoice_date": "2026-09-18",
  "due_date": "2026-09-30",
  "currency": "PHP",
  "subtotal": 22000.0,
  "tax": 2640.0,
  "total_amount": 24640.0
}
```

Monetary values currently use floating-point numbers in the AI-facing structured schema because this produces a Structured Outputs-compatible JSON schema.

Precise financial arithmetic in later business-rule phases can convert values to decimal representations before calculations.

### Structured Outputs and Validation

DocuFlow does not trust free-form LLM responses directly.

AI responses are validated against Pydantic schemas before the application uses or persists them.

Classification uses:

```text
DocumentClassification

document_type
confidence
```

Invoice extraction uses:

```text
InvoiceExtraction

invoice_number
supplier
invoice_date
due_date
currency
subtotal
tax
total_amount
```

The combined result is represented by:

```text
DocumentAnalysisResult

classification
extracted_data
```

This provides a predictable contract between the AI layer and application services.

### AI Persistence

The `documents` table now stores:

```text
document_type
classification_confidence
extracted_data
```

`extracted_data` uses PostgreSQL `JSONB` so different document types can eventually store different structured field sets without creating many document-specific columns.

Example:

```json
{
  "invoice_number": "INV-2026-001",
  "supplier": "ABC Office Supplies",
  "invoice_date": "2026-09-18",
  "due_date": "2026-09-30",
  "currency": "PHP",
  "subtotal": 22000.0,
  "tax": 2640.0,
  "total_amount": 24640.0
}
```

Database changes are managed through Alembic migrations, including:

```text
classification_confidence column
extracted_data JSONB column
ai_processing enum value
analyzed enum value
ai_processing_failed enum value
```

### AI Processing Status Lifecycle

Successful AI analysis:

```text
text_extracted
↓
ai_processing
↓
analyzed
```

Failed AI analysis:

```text
text_extracted
↓
ai_processing
↓
ai_processing_failed
```

This distinguishes text-extraction failures from AI-analysis failures.

### AI API Error Handling

The analysis endpoint maps expected conditions to controlled responses:

```text
Document does not exist
→ 404 Not Found

Authenticated user does not own document
→ 403 Forbidden

Document is not ready for AI analysis
→ 400 Bad Request

AI provider is not configured
→ 503 Service Unavailable

Classification or extraction fails
→ 502 Bad Gateway

Successful analysis
→ 200 OK
```

Raw provider exceptions are not returned to API clients.

Internal AI-layer logging preserves provider errors for debugging.

### Real End-to-End AI Verification

Phase 7 was verified using a real invoice flow:

```text
Upload TXT invoice
↓
Extract text
↓
Real OpenAI classification request
↓
Classify as invoice
↓
Real structured invoice extraction request
↓
Persist AI results
↓
status = analyzed
```

This confirmed that the API, AI provider, Pydantic structured outputs, PostgreSQL persistence, and document-status lifecycle work together.

---

## AI Evaluations

AI evaluations are kept separately from normal `pytest` software tests.

```text
tests/
→ verifies software behavior using deterministic tests and mocks

evals/
→ measures real model quality using fixed ground-truth examples
```

Current evaluation commands:

```bash
python -m evals.run_classification_eval
python -m evals.run_invoice_extraction_eval
```

### Classification Evaluation

Current result:

```text
6 / 7 correct
85.71% accuracy
```

The current known miss is an `unknown` example classified as:

```text
memo
```

This result only measures performance on the current seven-case evaluation dataset.

It should not be interpreted as real-world classification accuracy.

### Invoice Extraction Evaluation

Current result:

```text
24 / 24 fields correct
100.00% field accuracy
```

This was measured across three invoice examples containing:

```text
complete fields
missing fields
invoice without tax
```

The extractor correctly preserved missing values as `None` rather than inventing values.

### Purpose of Evaluations

Evaluations provide a measurable baseline for future changes to:

```text
prompts
models
schemas
classification definitions
extraction strategies
```

For example:

```text
Change prompts.py
↓
Run relevant eval
↓
Compare with previous baseline
↓
Keep or revert change
```

This helps detect AI regressions instead of relying only on subjective manual testing.

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

The Docker container uses PostgreSQL's internal port:

```text
5432
```

Check running containers:

```bash
docker ps
```

---

## Backend Setup

Navigate to:

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

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-luna

TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5434/docuflow_test
```

Never commit real secrets from `.env`.

Generate a JWT secret with:

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

Development and production database schema changes should be applied through Alembic.

Some PostgreSQL-native enum changes require manually authored Alembic migration commands because enum-value additions may not be generated automatically.

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

The API is available at:

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

The database health endpoint verifies PostgreSQL connectivity using a lightweight SQL query.

---

## Testing

DocuFlow uses `pytest`.

Run the complete test suite:

```bash
pytest -v
```

### Health Tests

Current health testing includes:

* application health endpoint

### Authentication Service Unit Tests

Current authentication-service testing includes:

* successful registration
* duplicate email rejection
* successful login
* incorrect password rejection
* unknown email rejection
* inactive-user rejection

### Authentication API Integration Tests

Current authentication API testing includes:

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

### Document Upload Service Tests

Current testing includes:

* successful document upload
* unsupported extension rejection
* empty-file rejection
* oversized-file rejection
* file cleanup when database persistence fails

### Document Processing Service Tests

Current testing includes:

* successful text extraction
* persistence of extracted text
* transition to `text_extracted`
* transition to `processing_failed` when extraction fails

### TXT Extractor Tests

* successful text extraction
* missing-file rejection
* directory-path rejection

### DOCX Extractor Tests

* successful paragraph extraction
* empty-paragraph filtering
* missing-file rejection
* directory-path rejection

### PDF Extractor Tests

* missing-file rejection
* directory-path rejection

A dedicated successful PDF extraction fixture can be expanded later.

### Extractor Factory Tests

* TXT extractor selection
* DOCX extractor selection
* PDF extractor selection
* case-insensitive extension handling
* unsupported-extension rejection

### Document API Integration Tests

#### Upload

* successful authenticated upload
* authentication requirement
* unsupported extension rejection
* empty-file rejection
* document database-record creation
* physical file-storage verification
* safe API response verification

#### Processing

* successful authenticated document processing
* authentication requirement
* unknown document rejection
* cross-user processing rejection
* extracted-text persistence
* processing-status persistence

### AI Unit and Workflow Tests

Phase 7 testing includes:

* document-classifier success behavior
* empty classification input rejection
* missing parsed classification handling
* provider classification error conversion
* invoice-extractor success behavior
* empty invoice input rejection
* missing parsed extraction handling
* provider extraction error conversion
* missing optional invoice fields
* `DocumentAIService` orchestration
* supported and unsupported extraction routing
* persistent document-analysis workflow
* AI-processing status transitions
* AI failure-state handling

### Test Database

A separate PostgreSQL test database is used for integration testing:

```text
docuflow_test
```

This prevents automated tests from modifying the normal development database.

Temporary filesystem locations are also used during document tests to avoid polluting:

```text
backend/uploads/
```

### Current Test Result

After Phase 7 implementation:

```text
66 passed
```

The test suite currently covers:

* authentication
* authorization
* health checks
* document upload services
* document upload API behavior
* filesystem integration
* PostgreSQL persistence
* TXT extraction
* DOCX extraction
* PDF extractor validation
* extractor selection
* document-processing services
* document-processing API behavior
* processing-status transitions
* ownership authorization
* AI classification behavior
* invoice structured extraction behavior
* AI orchestration
* persistent AI-analysis workflow
* AI failure-state handling

---

## Code Quality

Ruff is used for Python linting and formatting.

Project-level Ruff configuration is stored in:

```text
backend/pyproject.toml
```

Run lint checks:

```bash
ruff check .
```

Check formatting:

```bash
ruff format --check .
```

Automatically fix supported lint issues:

```bash
ruff check . --fix
```

Format Python files:

```bash
ruff format .
```

After code-quality changes:

```bash
pytest -v
```

The FastAPI route layer includes a Ruff exception for rule `B008`, because FastAPI intentionally uses calls such as:

```python
Depends(...)
File(...)
```

inside function parameter defaults.

---

## Document Processing Pipeline

DocuFlow's planned workflow is:

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

The first three major stages are now implemented:

```text
Document Upload                  ✅
Text Extraction                  ✅
AI Classification & Extraction  ✅
```

The next stage is:

```text
Business Rule Validation
```

which will be introduced in Phase 8.

---

## Supported Document Types

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

Uploaded documents initially begin with:

```text
document_type = unknown
```

Phase 6 extracts machine-readable text.

Phase 7 classifies that text using the AI layer.

Structured extraction is currently implemented for invoices.

Additional document-specific extraction schemas can be added incrementally as requirements grow.

---

## Development Phases

```text
Phase 1  — Project Setup                         ✅ Completed
Phase 2  — Backend Foundation                    ✅ Completed
Phase 3  — Database Design                       ✅ Completed
Phase 4  — Authentication & Authorization        ✅ Completed
Phase 5  — Document Upload                       ✅ Completed
Phase 6  — Document Processing                   ✅ Completed
Phase 7  — AI Classification & Extraction        ✅ Completed
Phase 8  — Business Rules                        ← Next
Phase 9  — Workflow & Approval
Phase 10 — RAG / Document Q&A
Phase 11 — Dashboard & Audit Logs
Phase 12 — Frontend
Phase 13 — Testing
Phase 14 — Deployment / DevOps
```

The project is developed incrementally, with each phase implemented, tested, reviewed, documented, and committed before the next major phase begins.

---

## Phase 6 Completion Summary

Phase 6 introduced DocuFlow's document-ingestion and text-extraction pipeline.

Implemented:

```text
Base extractor interface
TXT extraction
DOCX extraction
PDF extraction
Extractor factory
Document processing service
Processing status transitions
Processing failure handling
Domain-specific processing errors
Authenticated processing endpoint
Document ownership authorization
PostgreSQL extracted-text persistence
Processing unit tests
Processing API integration tests
Ruff project configuration
```

Current Phase 6 flow:

```text
Uploaded Document
↓
POST /documents/{document_id}/process
↓
Authentication
↓
Document Lookup
↓
Ownership Authorization
↓
status = processing
↓
Extractor Factory
↓
TXT / DOCX / PDF Extractor
↓
Extracted Text
↓
Save extracted_text
↓
status = text_extracted
↓
Document Ready for AI Classification
```

---

## Phase 7 Completion Summary

Phase 7 introduced DocuFlow's first production-style LLM integration for document classification and structured extraction.

Implemented:

```text
OpenAI provider configuration
Dedicated AI client layer
Document classification prompt
Structured invoice extraction prompt
Pydantic structured-output schemas
DocumentClassifier
InvoiceExtractor
AI-specific controlled exceptions
DocumentAIService orchestration
DocumentAnalysisService persistent workflow
AI processing status lifecycle
AI analysis endpoint
Document ownership enforcement
AI API error handling
classification_confidence persistence
JSONB extracted_data persistence
Alembic migrations for AI fields and statuses
Real OpenAI end-to-end verification
Classification evaluation suite
Invoice extraction evaluation suite
```

Current Phase 7 flow:

```text
Document with extracted text
↓
POST /documents/{document_id}/analyze
↓
Authentication
↓
Document Lookup
↓
Ownership Authorization
↓
Validate status = text_extracted
↓
status = ai_processing
↓
Document Classifier
↓
Validated DocumentClassification
↓
If invoice:
Invoice Extractor
↓
Validated InvoiceExtraction
↓
Persist document_type
↓
Persist classification_confidence
↓
Persist extracted_data
↓
status = analyzed
```

Current quality baseline:

```text
Software tests:
66 passed

Classification eval:
6 / 7 correct
85.71% on current evaluation set

Invoice extraction eval:
24 / 24 fields correct
100.00% on current evaluation set
```

DocuFlow is now ready to move into:

```text
Phase 8 — Business Rules
```

Phase 8 will consume validated Phase 7 structured data and apply deterministic company rules to decide what should happen next.
