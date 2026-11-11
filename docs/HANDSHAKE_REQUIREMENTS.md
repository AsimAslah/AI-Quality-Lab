# Handshake Requirements Evidence Map

## 1. Solve a real productivity problem

**Implemented:** A reviewer submits a prompt, candidate response, optional reference, and weighted rubric. The system evaluates measurable criteria, identifies possible PII, calculates a report, saves it, and makes it reviewable later.

**Evidence:** `POST /api/evaluations`, the New Evaluation page, `app/evaluator.py`, `app/pii.py`, Results, History, and JSON/Markdown export. `test_valid_submission_persists_report_and_real_events` verifies the end-to-end workflow.

## 2. Full-stack architecture with persistent data

**Implemented:** React/TypeScript frontend, FastAPI/Pydantic backend, SQLAlchemy database layer, Replit PostgreSQL `DATABASE_URL`, server-side validation, ownership-scoped APIs, transactional persistence, and error handling.

**Evidence:** `src/`, `app/`, `app/models.py`, `app/api.py`, `.replit`. Isolation and persistence are verified by `test_event_and_run_isolation_between_browser_owners` and `test_dashboard_and_history_restore_persisted_state`.

Local SQLite is an explicit developer fallback; Replit deployment instructions require its managed production database.

## 3. Live “How It Works” diagram

**Implemented:** Eight React Flow nodes update from genuine stored server events over SSE. Nodes show status, measured duration, latest message, and architectural layer. The stage inspector exposes safe metadata/errors. No simulated work delays are used.

**Evidence:** `app/pipeline.py`, `GET .../stream`, `ExecutionGraph.tsx`, `RunPage.tsx`. Event stage coverage, uniqueness, order, and durations are asserted in `test_valid_submission_persists_report_and_real_events`.

## 4. Handle failures and recover intelligently

**Implemented:** Pydantic validation, idempotency constraint, transaction rollback/retry, provider timeout and bounded retry, deterministic fallback, PII provider gate, stored failure events, preserved submissions, refresh/reconnect restoration, and development-only failure injection.

**Evidence:** `EventRecorder`, `process_evaluation`, owner/idempotency constraints, SSE `after` sequence, and tests for invalid input, duplicate keys, sensitive-data redaction, timeout/retry/recovery, and state restoration.

Recovery is never reported as successful unless fallback execution continues and a report is persisted.

## 5. Public deployment

**Prepared and locally verified:** Vite production build, FastAPI static serving, port `5000`, `.replit` build/run commands, managed database configuration, environment template, security headers, responsive layout, and `/api/health`.

**Manual remaining step:** Publish from the owner’s Replit account, create/select the production database, and verify the resulting public URL. The project does not claim this step is complete without that observation.

See `docs/DEPLOYMENT.md` for the exact checklist.
