# Prioritized Implementation Plan

## Phase 1 — Research and architecture

- [x] Inspect repository and working tree (empty repository, no unrelated work).
- [x] Verify current Replit database, deployment, configuration, pricing, and plan guidance.
- [x] Define product scope, event schema, data model, recovery behavior, and deployment topology.
- [x] Write PRD, architecture, schema, and implementation plan.

## Phase 2 — Foundation (P0)

- [x] Create FastAPI application, configuration, security middleware, SQLAlchemy models, and migrations/bootstrap.
- [x] Create React/Vite/TypeScript client, route shell, theme, API client, and shared design system.
- [x] Add Replit build/run configuration and environment template.

Milestone check: health endpoint reaches a real database and production frontend assets are served by FastAPI.

## Phase 3 — Core workflow (P0)

- [x] Add strict submission schemas and ownership-scoped CRUD endpoints.
- [x] Implement PII scanner, deterministic rubric evaluators, weighted scoring, evidence, and limitations.
- [x] Persist authorized submissions and reports.
- [x] Build New Evaluation, Results, Dashboard, and History experiences.

Milestone check: distinct inputs create distinct persisted reports, and unauthorized owner sessions receive 404.

## Phase 4 — Observability and replay (P0)

- [x] Record real stage transitions, timestamps, safe metadata, and monotonic durations.
- [x] Stream stored events over resumable SSE.
- [x] Render the live React Flow execution diagram and stage inspector.
- [x] Build replay state machine with play/pause/restart/speed.

Milestone check: refresh restores the graph; replay reproduces stored ordering and keeps original timing data.

## Phase 5 — Reliability and privacy (P0)

- [x] Add idempotency, transaction retries, rate limiting, error redaction, and secure headers.
- [x] Add optional provider interface, timeouts, retry/backoff, schema validation, PII gate, and real deterministic fallback.
- [x] Add development-only, secret-gated failure scenarios.
- [x] Document privacy behavior in product UI.

Milestone check: controlled provider timeout produces failed/retrying/recovered events and a reduced-capability report.

## Phase 6 — Quality (P0/P1)

- [x] Backend tests: valid/invalid submissions, persistence, event order/isolation/duration, idempotency, timeout/retry/fallback, input preservation, redaction, reconnection restoration.
- [x] Frontend graph reconstruction test plus browser verification of results, replay controls, and responsive graph fallback.
- [x] Type-check, build, pytest, dependency audit, production API smoke test, and targeted browser smoke test.
- [x] Fix all release-blocking defects found.

## Phase 7 — Deployment preparation (P0)

- [x] Verify production build and single-port start locally.
- [x] Add health/readiness behavior, `.replit`, `.gitignore`, `.env.example`, and exact manual publish steps.
- [x] Confirm database URL handling for Replit development and production databases.

## Phase 8 — Submission (P0)

- [x] Complete README, Handshake evidence map, test report, deployment guide, demo script, and accurate submission copy.
- [x] Record verified vs manual-only status; do not claim a live deployment without a verified URL.
- [x] Prepare a pull-request description and clean, secret-free Git state.

The remaining release-owner action is publishing through the Replit account and verifying the resulting public URL against `docs/DEPLOYMENT.md`.

## Deferred (P2)

- Authenticated account recovery, shared teams, reusable rubric library, run comparisons, distributed rate limiting, durable task queue, provider cost ledger, and fully independent factual-source retrieval.
