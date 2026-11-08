# DocuFlow AI

**AI-powered document processing, business-rule automation, human approval workflows, and retrieval-augmented question answering.**

DocuFlow AI is a full-stack application that helps teams intake business documents, extract readable text, classify document types, extract structured invoice data, apply deterministic business rules, route items for human review, and ask questions about stored documents with supporting source chunks.

It is implemented as a **modular monolith**: a React frontend communicates with a FastAPI backend organized into distinct API, service, domain, repository, security, AI, processing, storage, and persistence layers.

## Live Application

| Component | URL / provider |
| --- | --- |
| Frontend | [DocuFlow AI on Vercel](https://docuflow-ai-assistant.vercel.app) |
| Backend | [FastAPI on Render](https://docuflow-ai-backend-ankq.onrender.com) |
| API documentation | [Swagger UI](https://docuflow-ai-backend-ankq.onrender.com/docs) |
| Database | Supabase PostgreSQL with pgvector |
| Private document storage | Supabase Storage |
| LLM and embeddings | OpenAI API |

**Access:** Production self-registration is disabled (`PUBLIC_REGISTRATION_ENABLED=false`). Accounts are provisioned deliberately; demo credentials are not published. The backend still has an internet-accessible API, so disabling registration is **not** equivalent to restricting all public access.

**Free-tier note:** Render Free instances may spin down during inactivity, causing slow first requests. OpenAI usage is metered separately; free hosting does not make model calls free. The deployment is a portfolio demonstration, not a fully hardened enterprise service.

## Project Status — November 8, 2026

- **Phases 1–13:** Core application, frontend, workflow completion, and reliability work implemented; Phase 13 merged into `main`.
- **Phase 14.1–14.3:** GitHub Actions CI, validated production configuration, and Docker backend completed.
- **Phase 14.4:** Configurable local/Supabase Storage adapter implemented and merged; private cloud object storage integrated.
- **Phase 14.5:** Supabase PostgreSQL schema migrated; FastAPI deployed to Render; React/Vite deployed to Vercel; production CORS and SPA rewrite configured; controlled user provisioning demonstrated.
- **Phase 14.6 — CI/CD:** Protected `main` branch with required backend/frontend GitHub Actions checks; verified PR-to-production deployment with Vercel and Render.
- **Phase 15.1 — Admin User Listing:** Admin-only `GET /admin/users` with validated pagination and safe user response fields; merged in PR #15.
- **Phase 15.2 — Admin Role Management:** Admin-only `PATCH /admin/users/{user_id}/role`, role validation, self-change restriction, last-active-admin safeguards, atomic audit logging, PostgreSQL advisory locking, and API/concurrency tests. Merged in PR #16 and deployed to Render at commit `02b4075` on November 8, 2026.
- **Phase 15.3 — Planned:** Admin account activation/deactivation, including last-active-admin protection and auditability. Dedicated Admin UI remains planned.
- **Production:** Supabase Alembic revision `27ba877ff4bc` applied; Render deployment live; `/health` and `/health/database` healthy. A successful production role-change operation has not yet been demonstrated.
- **Verified cloud document path:** Production sign-in; authenticated PDF upload; text extraction; AI invoice classification/analysis; document indexing; question answering with a retrieved source chunk.
- **Not yet fully verified in the deployed environment:** Complete manager/admin approval and information-request journeys, role-change functional smoke test, broader concurrency/failure recovery, backup restoration, load tests, and security/operational controls described below.

### Latest recorded checks

| Check | Result | Scope |
| --- | --- | --- |
| Backend pytest | **11 Admin Role Management API tests passed**; **1 concurrency test passed across four runs** | Focused local checks; full post-Phase-15 regression count not supplied |
| GitHub Actions | Backend and frontend CI **passed** | PR #16, November 8, 2026 |
| Frontend Vitest | **51 passed across 10 files** | PR #16 CI report |
| Backend Ruff | Role-management test lint and format checks passed | Focused local verification; CI backend quality job passed |
| Production health | `/health` → healthy | Render |
| Database health | `/health/database` → connected | Render to Supabase PostgreSQL |
| Production public registration | `POST /auth/register` → **403** | `PUBLIC_REGISTRATION_ENABLED=false` |
| Production RAG demonstration | Indexed invoice, generated an answer, returned **Chunk 0** source | One manually tested synthetic invoice, not a broad evaluation |
| Phase 15.2 release | PR #16 merged; Render commit `02b4075` live; Supabase revision `27ba877ff4bc` | Health checks passed; production role-change request not yet exercised |

Earlier measurements of **90% backend coverage** and **96% workflow-history service coverage** are historical Phase 13 baselines, not freshly remeasured current coverage.

## Features

- **Authentication and roles:** JWT login; Argon2 password hashes; `employee`, `manager`, and `admin` authorization; protected frontend routes; configurable public registration.
- **Admin user directory:** Admin-only paginated user listing with role and active-status fields; no password hashes in responses.
- **Admin role management:** Admin-only role updates with typed validation, protection against self-role changes and last-active-admin loss, transactionally consistent audit records, and PostgreSQL locking for cooperating concurrent role changes.
- **Secure document intake:** Authenticated PDF, DOCX, and TXT upload; 10 MB maximum; generated internal storage keys; metadata in PostgreSQL; private storage adapter for local files or Supabase Storage.
- **Text extraction:** Extracts machine-readable text from TXT, DOCX, and text-based PDF files; maintains processing states and controlled errors. Scanned/image-only PDFs are not currently OCR-enabled.
- **AI classification:** OpenAI Responses API classification with validated Pydantic output. Supported types include invoice, contract, SOP, HR form, purchase request, policy, business report, support ticket, digital form, memo, and `unknown`.
- **Invoice extraction:** Validated invoice number, supplier, dates, currency, subtotal, tax, and total amount. Missing values can remain null.
- **Deterministic business rules:** Invoice totals above **20,000** are routed for manager approval; invoices with missing totals require manual review. Unsupported detailed rule types also fall back to review rather than automatic approval.
- **Human-in-the-loop workflows:** Manager/admin approval or rejection, manual review of invoices, information requests and employee responses, decision history, and workflow authorization.
- **Document RAG:** Paragraph-aware chunking, OpenAI embeddings, PostgreSQL `vector(1536)`, cosine-similarity retrieval scoped to the document, grounded answer generation, and returned source chunks.
- **Dashboard and audit:** Role-restricted summaries, persistent audit events, and history for document and workflow actions.
- **Original-file access:** Authorized viewing/downloading through backend permission checks, without exposing private storage keys as public object URLs.

## Technology Stack

| Layer | Tools |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, Axios, CSS |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Authentication | JWT / PyJWT, `pwdlib` / Argon2, role-based access control |
| Data | PostgreSQL 16, Psycopg 3, JSONB, pgvector |
| AI | OpenAI Python SDK, Responses API, embeddings, Pydantic-validated structured outputs |
| File processing | `pypdf`, `python-docx`, text extraction, storage adapters |
| Cloud | Vercel (frontend), Render (Docker backend), Supabase (PostgreSQL and private Storage) |
| Quality | pytest, Ruff, Vitest, React Testing Library, Oxlint, TypeScript checks, GitHub Actions |
| Local infrastructure | Docker and Docker Compose |

## Architecture

```text

Browser (React + Vite on Vercel)

           |

           | HTTPS / JSON / JWT

           v

FastAPI modular monolith (Docker on Render)

  |-- API routes / auth dependencies / validation

  |-- Services / workflow orchestration

  |-- Processing / PDF, DOCX, TXT extraction

  |-- AI / classification, invoice extraction, Q&A

  |-- Business rules / deterministic decisions

  |-- RAG / chunking, embeddings, retrieval

  |-- Repositories / SQLAlchemy

  |-- Storage interface / provider selection

           |                       |

           v                       v

Supabase PostgreSQL + pgvector   Private Supabase Storage

           ^

           |

      Audit and workflows

External model calls: OpenAI API (Responses + embeddings)

```

**Separation of concerns**

| Directory | Responsibility |
| --- | --- |
| `backend/app/api/routes/` | HTTP endpoints and response handling |
| `backend/app/api/dependencies.py` and `backend/app/security/` | Authentication and access policies |
| `backend/app/schemas/` | Validated input/output contracts |
| `backend/app/services/` | Application orchestration and workflow coordination |
| `backend/app/business_rules/` | Deterministic company policy; no LLM decisions |
| `backend/app/ai/` | OpenAI calls, prompts, model output parsing |
| `backend/app/processing/` | File-to-text extraction |
| `backend/app/rag/` | Text chunking for retrieval |
| `backend/app/repositories/` | Database access |
| `backend/app/db/models/` | Persistent data models |
| `backend/app/storage/` | Pluggable file persistence: local and Supabase |
| `backend/migrations/` | Alembic database schema history |
| `backend/evals/` | AI behavior evaluation separate from deterministic tests |
| `backend/tests/` | Unit and integration tests |
| `frontend/src/api/` | Shared JWT-aware HTTP client and feature APIs |
| `frontend/src/pages/`, `components/`, `auth/` | UI pages, reusable components, protected navigation |
| `frontend/vercel.json` | SPA fallback rewrite to `/index.html` for direct client-route visits |

### Typical document lifecycle

```text

Sign in

  -> Upload PDF/DOCX/TXT

  -> Save private object and document metadata

  -> Extract text

  -> Classify (OpenAI) + extract supported fields

  -> Validate Pydantic output

  -> Apply deterministic business rules

  -> Create/update workflow

  -> Human review / approval where required

  -> Audit relevant actions

Optional document Q&A:

  extracted text -> chunks -> embeddings -> pgvector

  question -> embedding -> document-scoped retrieval

           -> context + LLM -> answer + cited source chunks

```

**Distinct state machines:** A document can have status `analyzed` while its separate workflow remains `pending_approval`. AI classification is not itself an approval decision.

## Business Rules and Human Review

For the current invoice MVP, the rule engine uses the validated extracted total:

| Condition | Result |
| --- | --- |
| Total missing | `manual_review` → `needs_review` |
| Total greater than 20,000 | `manager_review` → `pending_approval` |
| Total at or below 20,000 | `continue_processing` → `completed` |
| Document type without implemented specific rules | `manual_review` → `needs_review` |

Financial comparisons use `Decimal` in the rules layer. Managers/admins can approve, reject, or request more information as permitted by workflow state and role; manual invoice review can provide a verified total for re-evaluation. Workflows retain decision history and audit records. Employee access is scoped to owned documents; broader reviewer read access does not automatically grant editing rights to every document action.

## Database and Migrations

Main application tables:

- `users`, `documents`, `workflows`, `approvals`
- `workflow_reviews`, `workflow_information_requests`
- `audit_logs`, `document_chunks`

`documents.extracted_data` and `documents.business_rule_result` use JSONB. `document_chunks.embedding` is a 1536-dimensional pgvector column. `documents.storage_provider` records whether a file uses local or Supabase storage so existing and new objects can be resolved correctly.

**Current recorded Alembic head:** `27ba877ff4bc`. Revision `50266c3b2d03` introduced document storage-provider metadata; revision `27ba877ff4bc` adds `user_role_changed` to PostgreSQL `audit_action`. The latest revision was applied and confirmed on the Supabase production database before PR #16 was merged.

Schema changes are managed with Alembic, not application-startup `Base.metadata.create_all()` calls. Create/apply migrations deliberately, review them, and verify the target environment (the commands below modify **the database selected by `DATABASE_URL`**):

```bash

cd backend

alembic current

alembic upgrade head

```

**Production warning:** Use the intended production database connection only for controlled migrations; never run tests or migration commands against a production database unintentionally. Automated integration tests use a separate disposable test database. Automatic application deployment does not mean migrations are safely automated; Render Free does not have a configured pre-deploy migration command in this project. The Phase 15.2 Supabase migration was run manually ahead of merging PR #16. Plan migration execution, verified backups, and rollback explicitly. Removing a PostgreSQL enum value requires separate review, rather than assuming `alembic downgrade` can undo it.

## Key API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Application health |
| GET | `/health/database` | PostgreSQL connection health |
| POST | `/auth/register` | Registration, **disabled in deployed production** |
| POST | `/auth/login` | Authenticate and issue JWT |
| GET | `/auth/me` | Current authenticated user |
| GET | `/admin/users` | Admin-only user directory with `limit` and `offset` pagination |
| PATCH | `/admin/users/{user_id}/role` | Admin-only validated user role change and audit event |
| POST | `/documents` | Authenticated upload |
| GET | `/documents` | List permitted documents |
| GET | `/documents/{document_id}` | Authorized document details |
| POST | `/documents/{document_id}/process` | Extract text |
| POST | `/documents/{document_id}/analyze` | AI analysis + business rules + routing |
| POST | `/documents/{document_id}/index` | Create/recreate document vector index |
| POST | `/documents/{document_id}/ask` | Grounded Q&A with source chunks |
| GET | `/workflows` | List permitted workflows |
| GET | `/workflows/{workflow_id}` | Workflow details |
| POST | `/workflows/{workflow_id}/decision` | Approval/rejection/information request |
| POST | `/workflows/{workflow_id}/review` | Manual-review decision |
| GET | `/workflows/{workflow_id}/information-request` | Active information request |
| POST | `/workflows/{workflow_id}/information-response` | Employee response |
| GET | `/workflows/{workflow_id}/history` | Decision and response history |
| GET | `/dashboard/summary` | Authorized aggregate metrics |
| GET | `/audit-logs` | Authorized audit feed |
| GET | `/audit-logs/{entity_type}/{entity_id}` | Audit history for an entity |

Original-file view/download endpoints also exist; consult the running OpenAPI documentation for their exact paths and response contracts.

## Local Development

### Prerequisites

- Python 3.12 and a virtual environment
- Node.js and npm
- Docker Desktop (for local PostgreSQL with pgvector)
- Git
- OpenAI API credentials for actual model calls

From the repository root, start local PostgreSQL:

```bash

docker compose up -d

```

The local database is published on port `5434` (container port `5432`).

### Backend

```powershell

cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

```

Create `backend/.env` from `backend/.env.example`. Keep it outside version control. For local development, use separate application and test database URLs.

Example configuration **with placeholders only**:

```dotenv

APP_NAME=DocuFlow AI

APP_ENV=development

APP_DEBUG=true

PUBLIC_REGISTRATION_ENABLED=true

CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

DATABASE_URL=postgresql+psycopg://LOCAL_USER:LOCAL_PASSWORD@localhost:5434/docuflow_db

TEST_DATABASE_URL=postgresql+psycopg://LOCAL_USER:LOCAL_PASSWORD@localhost:5434/docuflow_test

JWT_SECRET_KEY=REPLACE_WITH_RANDOM_SECRET_AT_LEAST_32_CHARS

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

STORAGE_PROVIDER=local

OPENAI_API_KEY=YOUR_OPENAI_API_KEY

OPENAI_MODEL=YOUR_SUPPORTED_OPENAI_MODEL

OPENAI_EMBEDDING_MODEL=text-embedding-3-small

OPENAI_EMBEDDING_DIMENSIONS=1536

```

Generate a JWT secret locally, then copy it **only** into your private environment configuration:

```bash

python -c "import secrets; print(secrets.token_hex(32))"

```

Run local migrations and start FastAPI:

```bash

alembic upgrade head

uvicorn app.main:app --reload

```

Swagger: `http://127.0.0.1:8000/docs`.

### Frontend

From another terminal:

```powershell

cd frontend

npm ci

```

Create `frontend/.env.local` with:

```dotenv

VITE_API_BASE_URL=http://127.0.0.1:8000

```

Then:

```bash

npm run dev

```

Vite normally serves the local app at `http://localhost:5173`.

## Cloud Deployment and Configuration

### Production topology

1. **Supabase:** Managed PostgreSQL, pgvector extension, and a **private** `docuflow-documents` Storage bucket. Schema migrated to `27ba877ff4bc` (role-change audit enum; November 8, 2026). Database application connections use the Supabase-provided connection configuration; never invent a pooler hostname.

2. **Render:** Free Docker Web Service, deployed from the `backend` repository directory. `backend/Dockerfile` runs FastAPI/Uvicorn on port `8000`; health check `/health`.

3. **Vercel:** Hobby project deployed from `frontend`, Vite preset, output `dist`, with `VITE_API_BASE_URL` pointing to Render. `frontend/vercel.json` rewrites deep client routes to `/index.html`.

4. **Browser:** HTTPS frontend requests the HTTPS backend, includes JWT for authenticated operations, and relies on backend authorization for access control.

5. **OpenAI:** API credentials are available only in the backend environment; keys and Supabase server credentials must **never** be put in frontend `VITE_` variables.

### Render environment variable names

Configure these in Render's Environment settings (values omitted where sensitive):

```dotenv

APP_ENV=production

APP_DEBUG=false

PUBLIC_REGISTRATION_ENABLED=false

PORT=8000

CORS_ALLOWED_ORIGINS=["https://docuflow-ai-assistant.vercel.app"]

DATABASE_URL=YOUR_SUPABASE_POSTGRESQL_PSYCOPG_URL

JWT_SECRET_KEY=YOUR_PRIVATE_RANDOM_JWT_SECRET

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

STORAGE_PROVIDER=supabase

SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co

SUPABASE_SECRET_KEY=YOUR_PRIVATE_SUPABASE_SERVER_KEY

SUPABASE_STORAGE_BUCKET=docuflow-documents

OPENAI_API_KEY=YOUR_PRIVATE_OPENAI_API_KEY

OPENAI_MODEL=YOUR_SUPPORTED_OPENAI_MODEL

OPENAI_EMBEDDING_MODEL=text-embedding-3-small

OPENAI_EMBEDDING_DIMENSIONS=1536

```

Use the **Supabase base project URL** for `SUPABASE_URL`, **not** a URL ending in `/rest/v1` or `/storage/v1`. The SDK appends Storage paths itself. The production upload issue caused by an incorrectly combined `/rest/v1/storage/v1/...` path was resolved through environment configuration.

`DATABASE_URL` is a distinct PostgreSQL connection string. For remote pooling, copy the exact **Session pooler** host supplied by Supabase; use the `postgresql+psycopg://` driver and SSL as appropriate. Do not confuse it with `SUPABASE_URL` or `SUPABASE_SECRET_KEY`.

### Vercel environment configuration

```dotenv

VITE_API_BASE_URL=https://docuflow-ai-backend-ankq.onrender.com

```

Vite environment variables are embedded in the client bundle at build time and must never contain passwords, tokens, OpenAI keys, or Supabase service/secret keys.

### SPA routing

`frontend/vercel.json`:

```json

{

  "rewrites": [

    { "source": "/(.*)", "destination": "/index.html" }

  ]

}

```

The fallback prevents Vercel `404 NOT_FOUND` when directly visiting or refreshing React Router URLs such as `/login` and `/documents`.

### Continuous integration and deployment — Phase 14.6 verified

DocuFlow uses **GitHub Actions for CI** and the connected hosting platforms for **CD**. Production releases are initiated by merging an eligible pull request into `main`; the merge is a human decision, while deployment is automatic under the current hosting configuration.

```text

Feature branch -> pull request

         |

         v

GitHub Actions: Backend Tests and Quality + Frontend Tests and Build

         |

         v

GitHub ruleset: both checks required, PR required, branch up to date

         |

         v

Human merges PR into main

         |

         +--> Vercel: production React deployment

         |

         +--> Render: backend Docker deployment after CI checks pass

                    (when changes are relevant to backend/)

         |

         v

Production health checks, logs, and functional smoke tests

```

**Verified deployment settings (November 8, 2026):**

| Control | Current configuration |
| --- | --- |
| GitHub CI file | `.github/workflows/ci.yml` |
| CI triggers | Pull requests targeting `main`; pushes to `main` |
| Required GitHub checks | `Backend Tests and Quality`; `Frontend Tests and Build` |
| Branch ruleset | `Protect main - CI required` targeting `main`, active, PR required, checks required, branch freshness required, force pushes/deletions blocked |
| Vercel production branch | `main` |
| Vercel source directory | `frontend/` |
| Render connected branch | `main` |
| Render root directory | `backend/` |
| Render Auto-Deploy | `After CI Checks Pass` |
| Render Dockerfile | `backend/Dockerfile` |
| Render Pre-Deploy Command | Unavailable/locked on the current Free service; Alembic migrations are run separately |

**Observed verification:**

- **PR #12** changed `docs/cd-verification.md`. Required CI passed; merge commit `e323bbf` was automatically deployed to Vercel production and marked **Ready**. Render did not deploy for this documentation-only change outside its root directory.
- **PR #13** changed `backend/CD_VERIFICATION.md`. Required CI passed; after merging, Render displayed **New commit via Auto-Deploy** for commit `2f63117`, then **Deploy live**. The backend `/health` and `/health/database` endpoints both reported healthy.
- **PR #15** added Admin-only user listing with pagination and RBAC; merged into `main`.
- **PR #16** added Admin Role Management and audit logging. Both required CI jobs passed; the Supabase migration `27ba877ff4bc` was applied manually before the merge; Render reported **Deploy live** for merge commit `02b4075` on November 8, 2026. Both production health endpoints returned healthy results. The deployed role-update route still needs a controlled functional smoke test.
- Vercel created working preview deployments for the verification PRs; preview and production are separate environments.

This verifies the **successful release path**, not every possible failure scenario. Do not assume that a green CI run guarantees correct business behavior, that all deployment failures have been tested, or that migrations, production secrets, rollback, backups, alerting, and monitoring are fully automated.

**Root-directory behavior:** The Render service monitors code changes relevant to `backend/`, so a `docs/`-only PR is not an appropriate test of backend CD. The repository can keep separate frontend/backend release triggers without building both services for every documentation change.

**Release and rollback runbook (current manual procedure):**

1. Make changes on a feature branch; run relevant tests and review the diff for credentials or unrelated files.

2. Open a PR, review the required GitHub Actions jobs, and merge only when checks succeed.

3. Observe the Vercel production deployment and the Render backend deployment (if relevant); confirm the deployed commit IDs.

4. Verify `/health`, `/health/database`, relevant user journeys, and logs. A green health endpoint alone does not establish feature correctness.
5. For schema changes, confirm the exact Supabase project, current Alembic revision, backup availability, and migration compatibility before deploying dependent code. `27ba877ff4bc` was applied manually ahead of PR #16.
6. For failed releases, restore a known-good application version using the hosting platform; review database backward compatibility separately. A PostgreSQL enum addition is not automatically reversed by rolling back application code.

Temporary test files (`docs/cd-verification.md` and `backend/CD_VERIFICATION.md`) can be removed later through a separate reviewed PR after the verification has been recorded. The local `backend/scripts/` provisioning directory must not be staged indiscriminately; protect credentials and keep one-time operations controlled.

### Production verification achieved

- FastAPI health: healthy.
- Database health: connected to Supabase PostgreSQL.
- Production public registration: **HTTP 403**, as configured.
- Provisioned employee account: production sign-in successful.
- PR #16 Admin Role Management backend deployed on Render (`02b4075`); Supabase schema revision `27ba877ff4bc` verified. Production role-change behavior is not yet validated by a dedicated authorized smoke test.
- Synthetic invoice PDF: uploaded to private storage; text extracted; classified as invoice; analyzed; indexed; question answered with an included source chunk.

This proves one functioning cloud workflow. It does **not** establish production readiness for arbitrary files, users, high traffic, or all authorization roles.

## Testing and AI Evaluations

### Automated software checks

From `backend/`:

```bash

pytest -q

ruff check app tests

ruff format --check app tests

pytest --cov=app --cov-branch --cov-report=term-missing -q

```

From `frontend/`:

```bash

npm test

npm run lint

npm run build

npm audit

```

Automated software tests cover authentication and authorization, document operations, storage behavior, extraction, AI service wrappers, invoice rules, workflow transitions, history, audit records, database persistence, and selected failure/concurrency cases. Phase 15.2 includes 11 passing Admin Role Management API tests (authorization, validation, audit/no-op behavior, demotion, rollback) and a separate PostgreSQL concurrent-demotion test passed across four recorded runs. Production smoke testing complements—rather than replaces—these tests.

### Model-quality evaluations

From `backend/`:

```bash

python -m evals.run_classification_eval

python -m evals.run_invoice_extraction_eval

python -m evals.run_rag_eval

```

Historical controlled evaluation baselines:

| Evaluation | Recorded result | Important limitation |
| --- | --- | --- |
| Document classification | 6/7 = **85.71%** | Seven fixed examples; one unknown-type miss |
| Invoice extraction | 24/24 fields = **100%** | Three sample invoices, not production-scale accuracy |
| RAG | 5/5 retrieval; 5/5 answers | Five controlled questions, not broad real-world performance |

The RAG retrieval baseline improved from 4/5 to 5/5 on this fixed set after introducing paragraph-aware chunking. Model changes should be assessed with representative evaluations, not just a successful single document.

## Known Limitations and Operational Priorities

- **Public API exposure:** Registration is disabled, but the API remains internet reachable. Rate limits, login-abuse defenses, AI request quotas, and broader cost controls require review before allowing public use.
- **AI spending:** OpenAI requests may incur charges. Set appropriate account/project limits and alerts; do not assume alerts provide hard request blocking.
- **Cold starts:** Render Free may sleep after inactivity. The frontend Axios client currently uses a **10-second timeout**, which can be shorter than a cold-start delay. Revisit request-specific timeouts and user-facing retry handling if needed.
- **Synchronous AI operations:** Time-consuming processing and model operations may benefit from queues/workers, timeouts, retry policy, and observability later; none is implied to exist today.
- **Document compatibility:** Text-based PDFs work; scanned PDFs need OCR. Structured extraction and specific rules currently focus on invoices.
- **Role coverage:** Employee, Manager, and Admin roles exist; manager and admin still overlap in some document/workflow privileges. Admin-only user listing and role updates are implemented, but account activation/deactivation and a dedicated Admin UI are not yet implemented. Production employee document and RAG flow was demonstrated; cross-role approval, information-request, and role-change journeys still need targeted cloud verification.
- **Storage and recovery:** Supabase Storage is private; review retention, orphan-object cleanup, storage quota, backups, restoration, and failed-request reconciliation.
- **Privacy and logs:** Avoid genuine confidential customer documents in the public demo; use synthetic data. Avoid printing secret-bearing Pydantic settings or provider exception bodies. Rotate a secret immediately if exposed in logs or screenshots.
- **Security and release process:** Keep server secrets in Render, audit privileged Supabase database permissions, enforce least privilege, maintain PR/branch protections, and practice rollback and recovery. A basic release/rollback runbook is documented; a failed-release exercise remains pending.
- **CI/CD scope:** The successful PR-to-production release path is verified. Failure-injection exercises, complete deployment gating across all service types, monitoring/alerting, backup-restore tests, and database migration rollback remain future hardening work.

## Phase 15 — Admin User Management & RBAC Refinement

**Status: in progress.** Admin User Listing (PR #15) and Admin Role Management (PR #16) are implemented and merged into `main`. The backend for both is deployed; the dedicated Admin UI and account-status controls are not yet built.

**Goal:** Separate privileged account administration from ordinary workflow review without changing the modular-monolith architecture or implicitly revoking Manager/Admin business-workflow permissions.

### Phase 15.1 — Admin User Listing (completed)

- `GET /admin/users`, protected by `require_roles(UserRole.ADMIN)`.
- Bounded pagination with `limit` and `offset`, total count, and a response schema that omits password hashes.
- Employee/Manager requests are denied; existing user authentication and repository layers are reused.
- Implemented and merged through PR #15.

### Phase 15.2 — Admin Role Management (implemented and deployed)

- `PATCH /admin/users/{user_id}/role` accepts a validated `UserRoleUpdateRequest` with `employee`, `manager`, or `admin`.
- Only an authenticated, active Admin can change roles; self-role changes are disallowed. Missing users, invalid roles, and prohibited role changes receive appropriate HTTP errors.
- A guarded transaction updates the target role and writes the `USER_ROLE_CHANGED` audit event with actor, target, old role, and new role. No-op changes do not write a role-change event.
- PostgreSQL transaction-level advisory locking and row locks coordinate cooperating role-change transactions; a successful competing-demotion test left one active Admin and one audit event. Other role/activation paths must follow the same locking policy to preserve the invariant.
- Eleven API and rollback test cases passed; the independent-session concurrency case passed on four recorded runs. This is targeted evidence, not proof of all possible interleavings.
- Alembic revision `27ba877ff4bc` adds the `user_role_changed` audit enum. Applied manually to the production Supabase database before merging PR #16.
- PR #16 merged into `main` and deployed on Render as `02b4075`. `/health` and `/health/database` passed; a production role-change smoke test remains pending.

### Phase 15.3 — Next: Account Activation and Deactivation

Planned work (not implemented):

1. Admin-only account activate/deactivate operations with explicit request schemas and response contracts.
2. Protect the final active Admin; coordinate status changes with the same membership-locking protocol used for role changes.
3. Ensure deactivated users cannot use existing access tokens on protected endpoints; test login and token behavior.
4. Record account-status changes in the audit trail within the same transaction.
5. Cover authorization, invalid states, no-op behavior, rollback, last-Admin safety, concurrency, and regressions.
6. Add a dedicated Admin management interface after confirming the backend contracts and access policies.

### Remaining Phase 15 acceptance criteria

- Backend Admin user listing and role management implemented and CI-tested.
- Account activation/deactivation, privileged-account UI, and full cross-role regression/security checks remain future tasks.
- Production role-change authorization and mutation should be checked using a designated noncritical synthetic account rather than a real user's permissions.
- Deployment, migration, and failure-recovery procedures remain controlled and partially manual.

## Development History

| Phase | Scope | Status |
| --- | --- | --- |
| 1–3 | Setup, backend foundation, database design | Implemented |
| 4 | JWT authentication and authorization | Implemented |
| 5–6 | Upload and text processing | Implemented |
| 7–8 | AI classification/extraction and deterministic business rules | Implemented |
| 9 | Workflow and approvals | Implemented |
| 10 | RAG and document Q&A | Implemented |
| 11 | Dashboard and audit logs | Implemented |
| 12 | React frontend | Implemented |
| 12.5 | Manual review, information exchange, file access, history, UI redesign | Implemented |
| 13 | Automated testing and reliability hardening | Merged into `main` |
| 14.1–14.3 | CI, production configuration, local Docker | Implemented |
| 14.4 | Cloud storage adapter and provider persistence | Merged into `main` |
| 14.5 | Supabase/Render/Vercel deployment and cloud smoke testing | Deployed; final operational hardening pending |
| 14.6 | Protected PRs, GitHub Actions CI, automatic Vercel/Render production deployments | **Core CI/CD release path verified** |
| 15.1 | Admin-only user listing, pagination, and RBAC | **Merged in PR #15; deployed** |
| 15.2 | Role-management API, audit transactions, PostgreSQL locking, tests | **Merged in PR #16; deployed** |
| 15.3 | Admin account activation/deactivation and last-active-Admin protection | **Planned** |

The project is intentionally built phase by phase: **requirements → inspect code → design → implement → test → review → pull request → deploy → monitor → iterate**.

---

**Current scope:** Working, cloud-hosted portfolio MVP with verified CI/CD release path and documented engineering boundaries. The production document/Q&A path has been demonstrated. Phase 15.1 and 15.2 backend administration features are merged and deployed; account activation/deactivation and the Admin UI are still planned. Full enterprise hardening and cross-role production validation remain open engineering tasks.
