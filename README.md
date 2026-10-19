# DocuFlow AI
DocuFlow AI is an AI-powered document-processing and workflow automation system designed to automate business document intake, classification, extraction, business-rule evaluation, routing, approval, and retrieval.
The project is being built incrementally using a modular monolith architecture with clear separation between API routes, schemas, services, repositories, database models, security, file storage, document processing, AI logic, deterministic business rules, and tests.
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
* Phase 8 — Business Rules
* Phase 9 — Workflow & Approval
* Phase 10 — RAG / Document Q&A
* Phase 11 — Dashboard & Audit Logs

Implemented and in final verification:
* Phase 12 — Frontend

Next:
* Phase 13 — Testing
---
## Technology Stack
### Frontend
* React
* Vite
* TypeScript
* React Router
* Axios
* JWT-aware API client
* Role-aware protected routes
* Responsive CSS component styling
### Backend
* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
### Database
* PostgreSQL 16
* Psycopg
* PostgreSQL JSONB
* pgvector for vector embeddings and cosine-similarity retrieval
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
### Business Rules
* Deterministic Python business-rule evaluation
* Document-type-specific rule modules
* Central business-rules engine
* Pydantic-validated `BusinessRuleResult`
* Decimal conversion for financial rule comparisons
* PostgreSQL JSONB persistence for rule decisions
* Manual-review fallback for document types whose rules are not implemented yet
### Workflow & Approval
* Persistent document workflow records
* Deterministic mapping from business actions to workflow states
* Manager/admin approval authorization
* Human approval decision history
* Approval, rejection, and information-request transitions
* Workflow ownership visibility controls for employees
* PostgreSQL persistence for workflow and approval records
* FastAPI workflow retrieval and decision endpoints
### RAG / Document Q&A
* OpenAI embeddings
* Configurable embedding model through environment settings
* 1536-dimensional vector embeddings
* pgvector-backed document chunk storage
* Cosine-distance semantic retrieval
* Paragraph-aware text chunking with character-based fallback
* Configurable chunk size and overlap
* Document indexing service
* Grounded document Q&A generation
* Retrieved source chunks returned with generated answers
* Controlled fallback for unsupported questions
* Dedicated RAG evaluation suite
### Dashboard & Audit Logs
* Persistent audit-log records for important user and system actions
* Controlled audit actions and entity types through enums
* Audit events for upload, text extraction, AI classification, structured extraction, business rules, workflow creation, and human decisions
* Manager/admin audit-history API access
* Dashboard aggregation queries for document and workflow totals
* Document counts grouped by processing status and document type
* Workflow counts grouped by workflow status
* Manager/admin dashboard authorization
* Dedicated Phase 11 API integration tests
### Infrastructure & Development
* Docker
* Docker Compose
* pytest
* FastAPI TestClient
* Ruff
---
## Project Architecture
DocuFlow currently follows a modular monolith structure.

Phase 12 adds a separate React frontend that consumes the FastAPI application over HTTP.

```text
frontend/
├── src/
│   ├── api/
│   │   ├── auditLogApi.ts
│   │   ├── client.ts
│   │   ├── dashboardApi.ts
│   │   ├── documentApi.ts
│   │   └── workflowApi.ts
│   ├── auth/
│   ├── components/
│   │   ├── audit-logs/
│   │   ├── dashboard/
│   │   ├── documents/
│   │   ├── layout/
│   │   └── workflows/
│   ├── pages/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
```

```text
backend/
├── app/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   ├── embedder.py
│   │   ├── qa_generator.py
│   │   ├── prompts.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── audit_log_routes.py
│   │   │   ├── auth_routes.py
│   │   │   ├── dashboard_routes.py
│   │   │   ├── document_routes.py
│   │   │   ├── health_routes.py
│   │   │   └── workflow_routes.py
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── business_rules/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── invoice_rules.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── workflow.py
│   │   │   ├── approval.py
│   │   │   ├── audit_log.py
│   │   │   └── document_chunk.py
│   │   ├── base.py
│   │   ├── database.py
│   │   ├── enums.py
│   │   └── session.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   └── chunker.py
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── base_extractor.py
│   │   ├── text_extractor.py
│   │   ├── docx_extractor.py
│   │   ├── pdf_extractor.py
│   │   ├── extractor_factory.py
│   │   └── exceptions.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── document_repository.py
│   │   ├── workflow_repository.py
│   │   ├── approval_repository.py
│   │   ├── audit_log_repository.py
│   │   ├── dashboard_repository.py
│   │   └── document_chunk_repository.py
│   │
│   ├── schemas/
│   │   ├── ai_schema.py
│   │   ├── audit_log_schema.py
│   │   ├── auth_schema.py
│   │   ├── business_rule_schema.py
│   │   ├── dashboard_schema.py
│   │   ├── document_schema.py
│   │   └── workflow_schema.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── audit_log_service.py
│   │   ├── dashboard_service.py
│   │   ├── document_service.py
│   │   ├── document_processing_service.py
│   │   ├── document_ai_service.py
│   │   ├── document_analysis_service.py
│   │   ├── workflow_service.py
│   │   ├── document_chunking_service.py
│   │   ├── document_embedding_service.py
│   │   ├── document_indexing_service.py
│   │   ├── document_retrieval_service.py
│   │   └── document_qa_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_storage.py
│   │
│   └── main.py
│
├── evals/
│   ├── __init__.py
│   ├── classification_cases.py
│   ├── invoice_extraction_cases.py
│   ├── run_classification_eval.py
│   ├── run_invoice_extraction_eval.py
│   ├── rag_cases.py
│   └── run_rag_eval.py
│
├── migrations/
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── test_audit_log_api.py
│   ├── test_auth_api.py
│   ├── test_auth_service.py
│   ├── test_dashboard_api.py
│   ├── test_business_rule_engine.py
│   ├── test_document_api.py
│   ├── test_document_processing_service.py
│   ├── test_document_service.py
│   ├── test_document_classifier.py
│   ├── test_invoice_extractor.py
│   ├── test_invoice_rules.py
│   ├── test_document_ai_service.py
│   ├── test_document_analysis_service.py
│   ├── test_document_analysis_integration.py
│   ├── test_workflow_service.py
│   ├── test_workflow_api.py
│   ├── test_text_chunker.py
│   ├── test_document_chunking_service.py
│   ├── test_document_embedder.py
│   ├── test_document_embedding_service.py
│   ├── test_document_indexing_service.py
│   ├── test_document_retrieval_service.py
│   ├── test_document_chunk_repository.py
│   ├── test_document_qa_generator.py
│   ├── test_document_qa_service.py
│   ├── test_docx_extractor.py
│   ├── test_extractor_factory.py
│   ├── test_health.py
│   ├── test_pdf_extractor.py
│   └── test_text_extractor.py
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
Domain / Business Logic
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
Business Rules Engine
↓
Document-Specific Rules
↓
BusinessRuleResult
↓
Persist business-rule decision
↓
Workflow Service
↓
Workflow Repository / Approval Repository
↓
PostgreSQL
```
RAG indexing and document Q&A use dedicated retrieval layers:
```text
Processed Document
↓
Extracted Text
↓
Document Chunking Service
↓
Paragraph-Aware Text Chunker
↓
Document Chunks
↓
OpenAI Embeddings
↓
pgvector / PostgreSQL
↓
User Question
↓
Question Embedding
↓
Cosine-Similarity Search
↓
Top Relevant Document Chunks
↓
Document QA Generator
↓
Grounded Answer + Retrieved Sources
```
Security-specific functionality is kept inside the core security layer.
---
## Separation of Concerns
DocuFlow keeps responsibilities separated by layer.
```text
api/routes/
→ HTTP request and response handling
services/
→ application workflow orchestration
repositories/
→ database access and persistence
schemas/
→ validated data contracts
db/models/
→ database table structure and relationships
ai/
→ AI-provider logic, prompts, classification, extraction
processing/
→ deterministic file and text extraction
business_rules/
→ deterministic company/domain policy
rag/
→ text chunking and retrieval-oriented document preparation
workflow service
→ translates business-rule decisions into workflow state and coordinates approvals
storage/
→ physical file persistence
```
A new development phase does not automatically require a new folder.
A new package is introduced when the code represents a distinct responsibility that should remain isolated from the existing layers.
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
The `documents` table currently stores:
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
business_rule_result
summary
created_at
updated_at
```
### Document Chunks
Phase 10 introduced the document_chunks table for RAG indexing.
Each row stores:
```text
id
document_id
chunk_index
content
embedding
created_at
```
embedding uses PostgreSQL vector(1536) through pgvector.
The combination of document_id and chunk_index is unique.
Chunks belong to a document and are deleted automatically when their parent document is deleted.
The embedding column is nullable so chunk persistence can occur before external embedding generation succeeds.
### Structured JSONB Data
`extracted_data` stores structured AI extraction results.
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
`business_rule_result` stores the deterministic Phase 8 decision.
Example:
```json
{
  "requires_approval": true,
  "approval_role": "manager",
  "requires_manual_review": false,
  "next_action": "manager_review",
  "reason": "Invoice total exceeds the manager approval threshold."
}
```
The `business_rule_result` column is nullable so documents created before Phase 8 remain valid.
---
## Authentication & Authorization
Phase 4 introduced JWT-based authentication and role-based authorization.
### Authentication Endpoints
```text
POST /auth/register
POST /auth/login
GET  /auth/me
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
The endpoint requires authentication.
```text
Authorization: Bearer <access_token>
```
Anonymous users cannot upload documents.
### Supported File Types
```text
.pdf
.docx
.txt
```
### Maximum File Size
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
The storage layer generates a unique internal filename using a UUID rather than storing the file directly using its user-provided name.
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

### Document Detail Endpoint
Phase 12 introduced a read-only detail endpoint for workflow review:

```text
GET /documents/{document_id}
```

It returns the normal public document metadata plus review-facing fields:

```text
extracted_text
summary
classification_confidence
extracted_data
business_rule_result
```

Authorization:

```text
employee
→ may view only documents they uploaded

manager / admin
→ may view employee documents for workflow review
```

The endpoint does not expose internal storage fields such as `stored_file_name` or `file_path`.

Processing, analysis, indexing, and RAG Q&A endpoints keep their existing ownership restrictions; the broader manager/admin permission applies only to read-only document review.
### Upload Failure Cleanup
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
.txt  → TextExtractor
.docx → DOCXExtractor
.pdf  → PDFExtractor
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
before analysis begins.
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
Business Rules Engine
↓
Persist AI result
↓
Persist business-rule result
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
→ coordinates AI analysis, business rules, persistence, and document state
document_repository.py
→ persists AI results, business-rule results, and document statuses
```
Provider-specific logic is kept outside API routes and repositories.
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
The deterministic business-rule layer converts financial values using:
```python
Decimal(str(total_amount))
```
before financial comparisons.
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
---
## Business Rules
Phase 8 introduced deterministic business-rule evaluation after AI classification and structured extraction.
The AI is responsible for extracting facts.
The business-rule layer is responsible for deciding what should happen based on those facts.
```text
AI
→ What information is inside this document?
Business Rules
→ What should the system do based on that information?
Workflow & Approval
→ Carry out that decision
```
### Business Rules Architecture
```text
app/business_rules/
├── __init__.py
├── engine.py
└── invoice_rules.py
```
Supporting schema:
```text
app/schemas/business_rule_schema.py
```
Responsibilities:
```text
business_rule_schema.py
→ defines the validated BusinessRuleResult contract
engine.py
→ selects the appropriate document-specific rule evaluator
invoice_rules.py
→ contains deterministic invoice company-policy logic
DocumentAnalysisService
→ coordinates AI analysis, business-rule evaluation, and persistence
document_repository.py
→ persists the final decision
```
Business rules do not:
* call OpenAI
* handle HTTP
* query PostgreSQL directly
* create workflow records
* create approval records
### Business Rule Result
Phase 8 produces a structured decision containing:
```text
requires_approval
approval_role
requires_manual_review
next_action
reason
```
Example:
```json
{
  "requires_approval": true,
  "approval_role": "manager",
  "requires_manual_review": false,
  "next_action": "manager_review",
  "reason": "Invoice total exceeds the manager approval threshold."
}
```
### Business Actions
Current actions include:
```text
continue_processing
manager_review
manual_review
```
These values are controlled through `BusinessAction` rather than arbitrary strings.
### Invoice Business Rules
The current invoice MVP contains three deterministic paths.
#### Missing Invoice Total
```text
total_amount = null
↓
requires_manual_review = true
↓
next_action = manual_review
```
#### High-Value Invoice
Current MVP threshold:
```text
20,000
```
Rule:
```text
total_amount > 20,000
↓
requires_approval = true
↓
approval_role = manager
↓
next_action = manager_review
```
The threshold is represented using `Decimal`.
Example:
```text
20,000.00
→ continue_processing
20,000.01
→ manager_review
```
#### Normal Invoice
```text
total_amount <= 20,000
↓
requires_approval = false
↓
requires_manual_review = false
↓
next_action = continue_processing
```
### Unsupported Rule Types
Phase 7 can classify document types whose detailed Phase 8 rules have not yet been implemented.
For example:
```text
contract
sop
purchase_request
policy
```
These documents are not silently treated as approved.
Instead:
```text
rule type not implemented
↓
requires_manual_review = true
↓
next_action = manual_review
```
This provides a safe fallback while document-specific rules are added incrementally.
### Business Rule Persistence
The final rule result is serialized using:
```text
model_dump(mode="json")
```
and stored in:
```text
documents.business_rule_result
```
using PostgreSQL `JSONB`.
This allows Phase 9 to consume the deterministic decision later.
### Phase Boundary
Phase 8 ends with:
```text
evaluate document
↓
produce BusinessRuleResult
↓
persist decision
```
Phase 8 does not create actual workflow or approval records.
That belongs to Phase 9.
```text
Phase 8
DECIDE
Phase 9
ACT
```
---
## Workflow & Approval
Phase 9 turns deterministic Phase 8 decisions into persistent business-process state and human approval records.
The boundary is:
```text
Phase 8
DECIDE what should happen
↓
Phase 9
ACT on that decision
```
### Workflow Architecture
Phase 9 introduced:
```text
app/api/routes/workflow_routes.py
app/repositories/workflow_repository.py
app/repositories/approval_repository.py
app/schemas/workflow_schema.py
app/services/workflow_service.py
```
Responsibilities:
```text
workflow_routes.py
→ handles HTTP workflow retrieval and approval requests
workflow_schema.py
→ defines workflow and approval API contracts
workflow_service.py
→ maps business decisions to workflow states
→ validates approval-state transitions
→ coordinates approval persistence and workflow updates
workflow_repository.py
→ creates, retrieves, and updates workflow records
approval_repository.py
→ creates and retrieves human approval decisions
```
### Phase 8 to Phase 9 Mapping
The initial workflow state is derived from the validated `BusinessRuleResult`.
```text
continue_processing
→ completed
manager_review
→ pending_approval
manual_review
→ needs_review
```
The workflow service does not re-evaluate invoice totals or duplicate Phase 8 business rules.
### Workflow Statuses
Current controlled workflow states are:
```text
needs_review
needs_information
pending_approval
approved
rejected
completed
```
Document processing state and workflow state remain separate.
Example:
```text
Document.status = analyzed
Workflow.current_status = pending_approval
```
This means document analysis completed successfully while the business process is still waiting for a human decision.
### Approval Decisions
Current approval decisions are:
```text
approved
rejected
information_requested
```
A pending workflow may transition as follows:
```text
pending_approval
├── approved              → approved
├── rejected              → rejected
└── information_requested → needs_information
```
Approval records preserve the human decision, approver identity, optional comment, and creation time.
A pending approval request is represented by the workflow's `pending_approval` state. An `Approval` row is created only when a human decision is actually submitted.
### Workflow Endpoints
```text
GET  /workflows/{workflow_id}
POST /workflows/{workflow_id}/decision
```
`GET /workflows/{workflow_id}` requires authentication.
Current visibility rules:
```text
employee
→ may view workflows for documents they uploaded
manager
→ may view workflows
admin
→ may view workflows
```
`POST /workflows/{workflow_id}/decision` is restricted to:
```text
manager
admin
```
Employees receive `403 Forbidden` when attempting to submit approval decisions.
### Approval Request Example
```json
{
  "decision": "approved",
  "comment": "Approved for payment."
}
```
The client does not provide `approver_id`.
Instead:
```text
JWT
↓
get_current_user
↓
require_roles(manager, admin)
↓
current_user.id
↓
Approval.approver_id
```
This prevents a client from impersonating another approver.
### Workflow Persistence
Each document currently has at most one workflow because `workflows.document_id` is unique.
A workflow stores:
```text
id
document_id
current_status
priority
recommended_action
assigned_to
created_at
updated_at
```
Approval records store:
```text
id
workflow_id
approver_id
decision
comment
created_at
```
One workflow can preserve multiple human decisions over time through its approval relationship.
### Real End-to-End Phase 9 Verification
Phase 9 was manually verified through Swagger and PostgreSQL using a high-value invoice.
```text
Upload invoice
↓
Process text
↓
Real OpenAI classification and extraction
↓
Phase 8 business rules
↓
manager_review
↓
Workflow created
current_status = pending_approval
↓
Authenticated manager
↓
POST /workflows/{workflow_id}/decision
↓
Approval row created
↓
Workflow updated to approved
```
The manual verification confirmed a real response containing:
```text
workflow.current_status = approved
approval.decision = approved
approval.approver_id = authenticated manager
```
This verifies the real FastAPI route, authentication and role authorization, workflow service, repositories, SQLAlchemy relationships, and PostgreSQL persistence together.
---
## RAG / Document Q&A
Phase 10 introduced semantic document retrieval and grounded question answering.
The feature is split into two major operations:
```text
INDEXING
Processed document
→ chunk text
→ create embeddings
→ store chunks + vectors in PostgreSQL
QUESTION ANSWERING
User question
→ embed question
→ search similar chunks
→ build context
→ generate grounded answer
→ return answer + supporting chunks
```
### RAG Endpoints
```text
POST /documents/{document_id}/index
POST /documents/{document_id}/ask
```
Both endpoints require authentication and enforce document ownership.
### Document Indexing
Indexing requires extracted document text.
The indexing flow is:
```text
Document
↓
DocumentChunkingService
↓
TextChunker
↓
DocumentChunk rows
↓
DocumentEmbeddingService
↓
OpenAI embedding model
↓
1536-dimensional vectors
↓
pgvector persistence
```
Re-indexing replaces existing chunks for the document before storing a fresh index.
### Paragraph-Aware Chunking
The default chunking configuration is:
```text
chunk_size = 1000
chunk_overlap = 200
```
Structured documents prefer paragraph boundaries so related information remains together.
Plain unstructured text falls back to deterministic overlapping character chunks.
A single paragraph larger than the configured chunk size also falls back to character-based splitting.
### Embeddings
Embedding configuration is controlled through environment settings:
```env
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
```
Document chunks are embedded in batches and stored in PostgreSQL through pgvector.
Questions are embedded using the same embedding configuration.
### Semantic Retrieval
Retrieval is scoped to one document.
The repository:
```text
filters by document_id
↓
ignores chunks without embeddings
↓
orders chunks by pgvector cosine distance
↓
returns the top matching chunks
```
The current default retrieval limit is:
```text
top_k = 5
```
### Grounded Question Answering
The Q&A generator receives only:
```text
question
-
retrieved document context
```
The prompt instructs the model to answer only from that context and not invent unsupported information.
When the available context is insufficient, the expected fallback is:
```text
I could not find enough information in the document to answer that question.
```
### Question Response
The API returns both the answer and retrieved supporting chunks.
Example shape:
```json
{
  "answer": "Employees receive 15 days of annual leave per year.",
  "sources": [
    {
      "chunk_index": 0,
      "content": "Annual Leave ..."
    }
  ]
}
```
The returned sources provide retrieval traceability for the generated answer.
### Phase 10 End-to-End Verification
Phase 10 was manually verified through Swagger using a real PDF.
The verified flow was:
```text
Upload PDF
↓
Extract text
↓
Index document
↓
Chunk text
↓
Create real OpenAI embeddings
↓
Persist vectors in pgvector
↓
Ask document question
↓
Embed question
↓
Retrieve relevant chunks
↓
Generate grounded answer
↓
Return answer + sources
```
Unsupported-question behavior was also manually verified and correctly returned the insufficient-information fallback.
---
## Dashboard & Audit Logs
Phase 11 introduced system visibility through persistent audit history and dashboard summary metrics.
### Audit Log Events
DocuFlow records important business events using controlled AuditAction and AuditEntityType values.
Current audited events include:

USER_REGISTERED
USER_LOGGED_IN

DOCUMENT_UPLOADED
DOCUMENT_TEXT_EXTRACTED
DOCUMENT_CLASSIFIED
DOCUMENT_FIELDS_EXTRACTED

RULE_CHECK_COMPLETED

WORKFLOW_CREATED
WORKFLOW_APPROVED
WORKFLOW_REJECTED
WORKFLOW_INFORMATION_REQUESTED

Audit records store:

user_id
action
entity_type
entity_id
event_metadata
created_at

System-generated events may use user_id = null.
Audit metadata stores useful context without copying entire business records or extracted document contents.
### Audit Log Endpoints

```text
GET /audit-logs
GET /audit-logs/{entity_type}/{entity_id}
```

Both endpoints are restricted to:

```text
manager
admin
```

Employees receive `403 Forbidden`.

`GET /audit-logs` returns the general audit feed from newest to oldest for the Phase 12 Audit Logs page.

`GET /audit-logs/{entity_type}/{entity_id}` returns one entity's audit history in chronological order.
### Dashboard Summary Endpoint

GET /dashboard/summary

The dashboard is restricted to:

manager
admin

The current summary includes:

total_documents
documents_by_status
documents_by_type
total_workflows
workflows_by_status

Missing categories are normalized to 0 so the frontend receives a predictable response shape.
### Dashboard Flow

PostgreSQL

↓

Dashboard Repository

↓

COUNT / GROUP BY queries

↓

Dashboard Service

↓

DashboardSummaryResponse

↓

GET /dashboard/summary

### Phase 11 Audit Flow

Important user or system action

↓

Application Service

↓

AuditLogService

↓

AuditLog Repository

↓

audit_logs table

↓

Authorized audit-history API

---
## AI Evaluations
AI evaluations are kept separately from normal `pytest` software tests.
```text
tests/
→ verifies deterministic software behavior
evals/
→ measures real AI/model quality using fixed ground-truth examples
```
Current evaluation commands:
```bash
python -m evals.run_classification_eval
python -m evals.run_invoice_extraction_eval
python -m evals.run_rag_eval
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
### RAG Evaluation
The Phase 10 RAG evaluation uses a deterministic handbook-style document containing multiple unrelated sections so retrieval must rank competing chunks.
The final Phase 10 baseline is:
```text
Overall:   5 / 5 (100.00%)
Retrieval: 5 / 5 (100.00%)
Answers:   5 / 5 (100.00%)
```
The evaluation covers:
```text
direct factual retrieval
paraphrased questions
multiple competing document sections
top-ranked source validation
answer-content validation
equivalent answer wording such as "12" and "twelve"
```
An earlier baseline using raw character chunking produced:
```text
Overall:   4 / 5 (80.00%)
Retrieval: 4 / 5 (80.00%)
Answers:   5 / 5 (100.00%)
```
Paragraph-aware chunking improved the retrieval baseline from 80% to 100% on the current five-case evaluation set.
These results measure only the current controlled evaluation dataset and should not be interpreted as general real-world RAG accuracy.
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
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
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
### Phase 8 Migration
Phase 8 introduced:
```text
5aaeace5f9f9
```
Description:
```text
add business rule result to documents
```
It adds:
```text
documents.business_rule_result
```
as a nullable PostgreSQL `JSONB` column.
After applying Phase 8:
```bash
alembic current
```
should show:
```text
5aaeace5f9f9 (head)
```
### Phase 10 Migration
Phase 10 introduced:
```text
a8be8ba6519c
```
Description:
```text
add document chunks for rag
```
The migration enables the PostgreSQL vector extension when needed and creates the document_chunks table with a vector(1536) embedding column.
The development and test databases both require pgvector support.
The Docker PostgreSQL image used by the project is:
```text
pgvector/pgvector:pg16
```
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
#### AI Analysis and Business Rules
* authenticated invoice analysis
* AI result persistence
* business-rule execution
* `business_rule_result` JSONB persistence
* high-value invoice manager-review routing
* successful analyzed status through the HTTP API
#### Document Details / Workflow Review
* document owner can retrieve detailed document data
* unrelated employee receives `403 Forbidden`
* manager can review another user's document
* admin can review another user's document
* unknown document returns `404`
* authentication is required
* extracted text, summary, classification confidence, structured extraction, and business-rule data are returned
* internal storage fields remain hidden

The focused document API suite currently contains 24 passing tests.
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
### Business Rule Tests
Phase 8 testing includes:
* missing invoice total requires manual review
* high-value invoice requires manager approval
* invoice exactly at approval threshold continues processing
* invoice below approval threshold continues processing
* invoice routing through `BusinessRulesEngine`
* invoice without structured extraction is rejected
* unsupported rule types fall back to manual review
* `DocumentAnalysisService` returns a `BusinessRuleResult`
* business-rule persistence call verification
* PostgreSQL JSONB integration verification
* high-value invoice persistence
* missing-total persistence
* normal-invoice persistence
* unsupported document-type persistence
* HTTP-level business-rule integration
### Workflow Service Tests
Phase 9 service testing includes:
* manager-review action maps to `pending_approval`
* manual-review action maps to `needs_review`
* continue-processing action maps to `completed`
* duplicate workflow creation is rejected
* approved decisions map to `approved`
* rejected decisions map to `rejected`
* information requests map to `needs_information`
* approval decisions are rejected for workflows not waiting for approval
### Workflow API Integration Tests
Workflow API testing includes:
* authenticated workflow retrieval
* unknown workflow returns `404`
* employee cannot submit approval decisions
* manager can approve a workflow
* admin can approve a workflow
* manager can reject a workflow
* manager can request additional information
* non-pending workflow decisions return `409 Conflict`
* employee cannot view another user's workflow
* manager can view another user's workflow
* admin can view another user's workflow
* employee workflow listing is restricted to owned documents
* manager workflow listing includes cross-user workflows
* admin workflow listing includes cross-user workflows
* workflow listing requires authentication

The focused workflow API suite currently contains 15 passing tests.
### Workflow PostgreSQL Integration
The document-analysis integration suite verifies real workflow persistence for:
* high-value invoice → `pending_approval`
* invoice with missing total → `needs_review`
* normal invoice → `completed`
* unsupported document rule type → `needs_review`
### RAG Unit and Integration Tests
Phase 10 testing includes:
* paragraph-aware text chunking
* overlapping character fallback
* chunk validation rules
* document chunk persistence
* safe re-chunking behavior
* OpenAI embedding wrapper behavior
* embedding persistence
* document indexing orchestration
* pgvector cosine-similarity ranking
* cross-document retrieval isolation
* document retrieval service behavior
* grounded Q&A generation
* Q&A fallback when no chunks are available
* answer source serialization
* authenticated document indexing API behavior
* authenticated document Q&A API behavior
* ownership authorization for indexing and Q&A
### Audit Log Tests
Audit testing includes:
* manager can retrieve entity audit history
* admin can retrieve entity audit history
* employee audit-history access is rejected
* audit history is returned chronologically
* entities without audit history return an empty list
* manager can retrieve the general audit feed
* admin can retrieve the general audit feed
* employee access to the general audit feed is rejected
* unauthenticated general audit access is rejected
* the general audit feed is returned newest first
* workflow creation records an audit event
* approval, rejection, and information requests record the correct audit action
* document upload records `DOCUMENT_UPLOADED`
* successful text extraction records `DOCUMENT_TEXT_EXTRACTED`
* successful AI analysis records classification, extraction, and business-rule audit events
* failed operations do not create misleading success audit events

The focused audit-log API suite currently contains 10 passing tests.
### Dashboard API Integration Tests
Phase 11 dashboard testing includes:
* manager dashboard access
* admin dashboard access
* employee dashboard access rejection
* total document counts
* document counts grouped by status
* document counts grouped by type
* total workflow counts
* workflow counts grouped by status
* zero values for missing categories
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
The integration-test database is created from SQLAlchemy metadata and isolated using database transactions.
### Current Test Status
Focused Phase 12 regression suites currently verified:

```text
Workflow API: 15 passed
Audit Log API: 10 passed
Document API: 24 passed
```

Before committing Phase 12, run the complete local suite:

```bash
pytest -v
```

and record the exact full-suite count from that run.

Also verify backend formatting/linting and frontend production checks:

```bash
ruff format --check app tests
ruff check app tests
```

```bash
npm run lint
npm run build
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
* deterministic invoice business rules
* business-rule engine routing
* business-rule persistence
* PostgreSQL JSONB rule-result persistence
* business-rule API integration
* workflow-service state mapping
* duplicate-workflow protection
* workflow PostgreSQL persistence
* workflow retrieval authorization
* manager/admin approval authorization
* approval-record persistence
* approval/rejection/information-request state transitions
* invalid workflow transition handling
* document chunk persistence
* paragraph-aware chunking
* embedding generation and persistence
* pgvector similarity retrieval
* retrieval isolation by document
* RAG indexing orchestration
* grounded Q&A generation
* RAG source responses
* document indexing API behavior
* document Q&A API behavior
* audit-log persistence and retrieval
* audit-log role authorization
* document/workflow audit events
* dashboard aggregation queries
* dashboard role authorization
* dashboard API response counts
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
The backend processing and visibility stages are now implemented:
```text
Document Upload                  ✅
Text Extraction                  ✅
AI Classification & Extraction  ✅
Business Rule Validation         ✅
Workflow Routing & Approval      ✅
RAG / Document Q&A               ✅
Dashboard & Audit Logs           ✅
```
The Phase 12 frontend is now implemented and connected to the backend.

```text
Authentication / Role Routing     ✅
Dashboard                         ✅
Documents                         ✅
Document Upload / Process         ✅
AI Analyze                        ✅
RAG Index / Q&A                   ✅
Workflows                         ✅
Human Approval Decisions          ✅
Workflow Document Review          ✅
Audit Logs                        ✅
```

The next major phase is Phase 13 — Testing, after final Phase 12 regression verification and documentation.
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
Phase 8 contains detailed deterministic rules for invoices.
Phase 9 converts the resulting business action into a persistent workflow state and supports manager/admin approval decisions for workflows that require approval.
Phase 10 indexes extracted document text into pgvector and supports grounded semantic document Q&A with returned source chunks.
Phase 11 adds manager/admin dashboard summaries and persistent audit history for important document and workflow actions.
Other classified document types currently fall back to manual review until their structured extraction and document-specific business rules are implemented.
Additional document-specific extraction schemas and business rules can be added incrementally as requirements grow.
---
## Development Phases
```text
Phase 1  — Project Setup                       ✅ Completed
Phase 2  — Backend Foundation                  ✅ Completed
Phase 3  — Database Design                     ✅ Completed
Phase 4  — Authentication & Authorization      ✅ Completed
Phase 5  — Document Upload                     ✅ Completed
Phase 6  — Document Processing                 ✅ Completed
Phase 7  — AI Classification & Extraction      ✅ Completed
Phase 8  — Business Rules                      ✅ Completed
Phase 9  — Workflow & Approval                 ✅ Completed
Phase 10 — RAG / Document Q&A                 ✅ Completed
Phase 11 — Dashboard & Audit Logs              ✅ Completed
Phase 12 — Frontend                             ← Next
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
Pass validated data into Phase 8
```
Current AI quality baseline:
```text
Classification eval:
6 / 7 correct
85.71% on current evaluation set
Invoice extraction eval:
24 / 24 fields correct
100.00% on current evaluation set
```
---
## Phase 8 Completion Summary
Phase 8 introduced DocuFlow's deterministic business-rule layer.
The objective was to separate AI understanding from company policy.
```text
Phase 7
AI determines the facts
↓
Phase 8
Deterministic Python rules determine what should happen
↓
Phase 9
Workflow and approval logic will execute the decision
```
Implemented:
```text
Dedicated business_rules package
BusinessRuleResult Pydantic contract
BusinessAction controlled values
BusinessRulesEngine
Invoice-specific deterministic rules
Manager approval threshold
Decimal-based financial comparison
Manual-review handling for missing invoice totals
Continue-processing path for normal invoices
Manual-review fallback for unsupported document rule types
DocumentAnalysisService business-rule integration
business_rule_result JSONB persistence
Document repository persistence helper
Alembic migration for business_rule_result
Invoice-rule unit tests
BusinessRulesEngine unit tests
DocumentAnalysisService integration tests
Real PostgreSQL persistence tests
HTTP API integration verification
Real Swagger/OpenAI invoice verification
```
### Current Phase 8 Flow
```text
Validated DocumentAnalysisResult
↓
BusinessRulesEngine
↓
Determine document rule type
↓
Invoice Rules when document_type = invoice
↓
BusinessRuleResult
↓
Serialize to JSON-compatible data
↓
Persist business_rule_result
↓
status = analyzed
```
### Current Invoice Rules
```text
Missing total amount
→ manual_review
Total amount <= 20,000
→ continue_processing
Total amount > 20,000
→ manager_review
```
Example high-value invoice:
```text
Total Amount: 28,000
↓
BusinessRulesEngine
↓
Invoice Rules
↓
requires_approval = true
approval_role = manager
next_action = manager_review
```
### Unsupported Document Rules
If Phase 7 classifies a document successfully but Phase 8 does not yet have detailed rules for that type:
```text
Contract / SOP / Purchase Request / etc.
↓
BusinessRulesEngine
↓
manual_review
```
The system does not silently assume that unsupported documents have passed business validation.
### Persistence
Phase 8 stores its decision in:
```text
documents.business_rule_result
```
using PostgreSQL `JSONB`.
Migration:
```text
5aaeace5f9f9
add business rule result to documents
```
### Real End-to-End Verification
Phase 8 was manually verified through Swagger using a real invoice.
```text
Upload invoice
↓
Process text
↓
Real OpenAI classification
↓
Real structured invoice extraction
↓
Business Rules Engine
↓
High-value invoice rule
↓
manager_review
↓
Persist decision in PostgreSQL
```
This confirmed that the real FastAPI application, OpenAI integration, business-rule layer, repository layer, SQLAlchemy, Alembic-managed schema, and PostgreSQL database work together.
Phase 9 now consumes the deterministic Phase 8 decision and turns it into persistent workflow state and human approval records.
The intended boundary is:
```text
Phase 8
DECIDE
↓
Phase 9
ACT
```
---
## Phase 9 Completion Summary
Phase 9 introduced DocuFlow's persistent workflow-routing and human-approval layer.
The objective was to turn the deterministic Phase 8 decision into real business-process state.
```text
Phase 8
DECIDE
↓
BusinessRuleResult
↓
Phase 9
ACT
```
Implemented:
```text
WorkflowResponse and approval Pydantic schemas
Workflow repository
Approval repository
WorkflowService
BusinessAction → WorkflowStatus mapping
Duplicate-workflow protection
Persistent workflow creation during document analysis
Manager/admin approval authorization
Workflow retrieval endpoint
Approval decision endpoint
Approval record persistence
Workflow status updates after human decisions
Employee workflow ownership visibility controls
Manager/admin cross-user workflow visibility
Invalid workflow-state protection
Workflow service unit tests
Workflow API integration tests
Real PostgreSQL workflow persistence verification
Real Swagger approval verification
```
### Current Phase 9 Flow
```text
DocumentAnalysisService
↓
Validated BusinessRuleResult
↓
WorkflowService.create_from_business_rule(...)
↓
Map next_action to WorkflowStatus
↓
Persist Workflow
↓
If pending approval:
Manager/Admin submits decision
↓
WorkflowService.record_approval_decision(...)
↓
Persist Approval
↓
Update Workflow.current_status
```
### Initial Workflow Mapping
```text
continue_processing
→ completed
manager_review
→ pending_approval
manual_review
→ needs_review
```
### Human Approval Mapping
```text
approved
→ approved
rejected
→ rejected
information_requested
→ needs_information
```
### Authorization
Workflow retrieval currently enforces:
```text
employee
→ own document workflows only
manager
→ permitted
admin
→ permitted
```
Approval decisions enforce:
```text
employee
→ forbidden
manager
→ permitted
admin
→ permitted
```
The backend derives `approver_id` from the authenticated user instead of accepting it from the client.
### Phase 9 End-to-End Verification
The real Phase 9 flow was manually verified through Swagger.
A high-value invoice produced:
```text
manager_review
↓
workflow.current_status = pending_approval
```
An authenticated manager then submitted an approval decision:
```json
{
  "decision": "approved",
  "comment": "Approved during Phase 9 verification."
}
```
The application returned and persisted:
```text
workflow.current_status = approved
approval.decision = approved
approval.approver_id = authenticated manager
```
This confirms that Phase 7 AI analysis, Phase 8 deterministic decisions, Phase 9 workflow creation, role authorization, human approval, repositories, SQLAlchemy, and PostgreSQL operate together as one application flow.
---
## Phase 10 Completion Summary
Phase 10 introduced DocuFlow's RAG-based semantic document retrieval and grounded question-answering layer.
Implemented:
```text
pgvector-enabled PostgreSQL
document_chunks database model
Alembic migration for document chunks and vector support
Document-to-chunk relationship
Paragraph-aware TextChunker
Character-based chunking fallback
Chunk persistence repository
OpenAI embedding wrapper
DocumentEmbeddingService
DocumentIndexingService
Cosine-similarity pgvector retrieval
DocumentRetrievalService
Grounded DocumentQAGenerator
DocumentQAService
Document indexing endpoint
Document question-answering endpoint
Answer source chunks
Ownership authorization for RAG endpoints
Controlled unsupported-question fallback
RAG unit and integration tests
Real PDF Swagger verification
Dedicated RAG evaluation suite
```
### Current Phase 10 Flow
```text
Processed Document
↓
POST /documents/{document_id}/index
↓
TextChunker
↓
DocumentChunk rows
↓
OpenAI embeddings
↓
pgvector
↓
POST /documents/{document_id}/ask
↓
Embed question
↓
Cosine-similarity retrieval
↓
Top relevant chunks
↓
DocumentQAGenerator
↓
Grounded answer + sources
```
### RAG Evaluation Baseline
The final controlled Phase 10 evaluation produced:
```text
Overall:   5 / 5 (100.00%)
Retrieval: 5 / 5 (100.00%)
Answers:   5 / 5 (100.00%)
```
The retrieval baseline improved from 80% to 100% after replacing raw character-only chunking with paragraph-aware chunking while retaining character fallback behavior.
The full regression suite also passed:
```text
131 passed
```
Manual Swagger verification confirmed successful real-PDF indexing, semantic retrieval, grounded question answering, source return, and unsupported-question handling.
DocuFlow is now ready to move into:
```text
Phase 11 — Dashboard & Audit Logs
```
---
## Phase 11 Completion Summary
Phase 11 introduced DocuFlow's dashboard summary and persistent audit-history layer.
The objective was to make important system activity both visible and traceable without mixing reporting or audit behavior into API routes or repositories that serve other responsibilities.
Implemented:

AuditLog repository

AuditLog service

AuditLog response schema

Audit-history API route

Manager/admin audit-history authorization

DOCUMENT_UPLOADED audit event

DOCUMENT_TEXT_EXTRACTED audit event

DOCUMENT_CLASSIFIED audit event

DOCUMENT_FIELDS_EXTRACTED audit event

RULE_CHECK_COMPLETED audit event

WORKFLOW_CREATED audit event

WORKFLOW_APPROVED audit event

WORKFLOW_REJECTED audit event

WORKFLOW_INFORMATION_REQUESTED audit event

Dashboard repository

Dashboard aggregation queries

Dashboard service

Dashboard response schemas

Dashboard summary API route

Manager/admin dashboard authorization

Document totals

Document counts by status

Document counts by type

Workflow totals

Workflow counts by status

Audit-log API integration tests

Dashboard API integration tests

Full regression verification

Ruff lint and format verification

### Current Audit Flow

Document / Workflow Action

↓

Application Service

↓

AuditLogService

↓

AuditLog Repository

↓

PostgreSQL audit_logs

↓

GET /audit-logs/{entity_type}/{entity_id}

↓

Manager / Admin

Audit records answer:

Who performed the action?

What happened?

What entity was affected?

Which entity record was affected?

What useful extra context exists?

When did it happen?

System-generated actions use a nullable user identity when no human directly performed the event.
### Current Dashboard Flow

Documents + Workflows

↓

PostgreSQL aggregation

↓

Dashboard Repository

↓

Dashboard Service

↓

DashboardSummaryResponse

↓

GET /dashboard/summary

↓

Manager / Admin

The current dashboard response reports:

total_documents

documents_by_status

documents_by_type

total_workflows

workflows_by_status

Missing statuses and document types are represented as zero values so Phase 12 can render the dashboard without special handling for missing keys.
### Phase 11 Authorization

employee

→ dashboard forbidden
→ audit-history API forbidden

manager

→ dashboard permitted
→ audit-history API permitted

admin

→ dashboard permitted
→ audit-history API permitted

### Phase 11 Verification
Phase 11 was verified with focused API and service tests plus the full regression suite.
Verification covered:

audit event creation

audit event retrieval

chronological audit history

role authorization

document audit integration

AI-analysis audit integration

workflow-decision audit integration

dashboard document counts

dashboard workflow counts

zero-value normalization

FastAPI route registration

full pytest regression

Ruff linting

Ruff formatting

The exact final test count should be recorded from the latest local pytest -v output when committing the completed phase.
DocuFlow is now ready to move into:

Phase 12 — Frontend

---

## Phase 12 Frontend Implementation Summary
Phase 12 introduced DocuFlow's authenticated React frontend and connected the previously completed backend features into one usable application.

### Implemented
```text
React + Vite + TypeScript application shell
React Router navigation
JWT token persistence
Axios request interceptor
Authenticated route protection
Role-aware route protection
Role-aware sidebar navigation
Login flow
Dashboard summary page
Document listing
Document upload
Document processing
AI analysis action
RAG indexing
Document Q&A with source chunks
Workflow listing
Manager/admin workflow decisions
Workflow document-review details
Audit-log feed
Loading, empty, success, and error states
Production TypeScript build verification
Frontend lint verification
```

### Frontend Authentication Flow
```text
Login
↓
POST /auth/login
↓
Persist JWT
↓
GET /auth/me
↓
Resolve authenticated user + role
↓
Protected application layout
↓
Role-aware navigation
```

Employees are routed to document-oriented functionality.

Managers and administrators additionally receive access to dashboard and audit-log screens.

### Document Frontend Flow
```text
Documents Page
↓
GET /documents
↓
Upload
↓
POST /documents
↓
Process
↓
POST /documents/{document_id}/process
↓
Analyze
↓
POST /documents/{document_id}/analyze
↓
Index
↓
POST /documents/{document_id}/index
↓
Ask
↓
POST /documents/{document_id}/ask
↓
Grounded answer + source chunks
```

The document list also exposes the derived `is_indexed` state so the frontend can decide whether to show Index or Ask actions.

### Workflow Frontend Flow
```text
Workflows Page
↓
GET /workflows
↓
Employee
→ own workflows only

Manager / Admin
→ all workflows
↓
Pending Approval
↓
Review
↓
GET /documents/{document_id}
↓
Document metadata
AI classification confidence
Structured extracted data
Business-rule result
Extracted text
↓
Human Decision
↓
POST /workflows/{workflow_id}/decision
↓
Approved / Rejected / Needs Information
```

The decision controls remain disabled while document details are unavailable, so managers do not approve a workflow without the review context successfully loading.

### Audit Logs Frontend Flow
```text
Manager / Admin
↓
Audit Logs Page
↓
GET /audit-logs
↓
Newest audit events first
↓
Action
Entity
Entity ID
User / System
Metadata
Timestamp
```

Entity-specific chronological history remains available through:

```text
GET /audit-logs/{entity_type}/{entity_id}
```

### Dashboard Frontend Flow
```text
Manager / Admin
↓
GET /dashboard/summary
↓
Document totals
Document counts by status
Document counts by type
Workflow totals
Workflow counts by status
↓
Dashboard cards / summaries
```

### Phase 12 Backend Support Added
The frontend required a small number of read-oriented backend extensions:

```text
GET /workflows
GET /audit-logs
GET /documents/{document_id}
```

`GET /documents/{document_id}` uses a dedicated `DocumentDetailResponse` instead of expanding the lightweight list response.

Review-facing fields include:

```text
extracted_text
summary
classification_confidence
extracted_data
business_rule_result
```

Internal storage fields remain private.

### Phase 12 Focused Regression Verification
Current focused backend results:

```text
Workflow API: 15 passed
Audit Log API: 10 passed
Document API: 24 passed
```

Frontend verification has included:

```text
npm run lint
npm run build
```

Before the Phase 12 commit, run the complete backend regression suite and final lint/build commands and record the exact full-suite result.

### Phase 12 Status
The Phase 12 feature implementation is complete and is in final regression verification.

Next:

```text
Phase 13 — Testing
```
