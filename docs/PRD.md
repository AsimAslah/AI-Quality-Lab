# AI Quality Lab — Product Requirements Document

## Product statement

AI Quality Lab helps reviewers evaluate an AI response against a reusable, weighted rubric while exposing the evidence, limitations, privacy findings, and real execution path behind the result.

**Tagline:** Evaluate AI responses. Understand every decision.

## Problem and users

Reviewers repeatedly perform the same mechanical checks—required phrases, response shape, instruction cues, privacy exposure, and weighted scoring—then manually document the result. This is slow and inconsistent. The primary users are AI product engineers, QA analysts, prompt engineers, educators, and portfolio reviewers.

The product does not claim that string heuristics prove truthfulness, relevance, or freedom from hallucinations. Every criterion is labeled as deterministic, heuristic, or model-assisted.

## Goals

1. Complete a useful response-evaluation workflow in under a minute.
2. Make every processing stage inspectable through genuine backend events and measured durations.
3. Persist submissions, reports, and execution events for history and replay.
4. Recover transparently from optional model-provider failure without losing deterministic results.
5. Isolate private records between anonymous visitor sessions.
6. Remain usable without an external AI key.

## Non-goals

- Proving factual accuracy without an authoritative source.
- Replacing expert review for safety-critical decisions.
- Multi-tenant enterprise identity, billing, or team administration in the challenge release.
- Sending detected sensitive text to third-party AI providers by default.

## Core user journey

1. A visitor opens the app and receives an opaque, HTTP-only ownership session.
2. They enter the original prompt, response, optional reference/context, and one or more weighted criteria.
3. The API validates size and shape, applies idempotency protection, and saves a run.
4. The browser moves to Live Execution and opens an SSE stream.
5. Eight real processing stages emit ordered, persistent events.
6. Deterministic checks and privacy scans run. Optional model evaluation runs only when enabled and safely configured.
7. The report shows a weighted score, criterion evidence, privacy findings, caveats, and capability labels.
8. The visitor can reopen the result from History or replay the recorded event sequence with play, pause, restart, and speed controls.

## Functional requirements

### Submission

- Prompt and response are required; reference/context is optional.
- Rubric contains 1–12 criteria, each with a name, description, 1–10 weight, evaluation mode, and optional required phrases.
- Inputs have explicit server-side limits and actionable validation errors.
- A client-provided idempotency key prevents accidental duplicate execution.
- The form preserves entered content when validation or network calls fail.

### Evaluation

- Validate response length and basic structure.
- Detect common PII patterns (email, phone, payment card candidates, API-key-like secrets, and IP address) without writing raw matches to event logs.
- Evaluate required phrases deterministically.
- Evaluate structural and instruction-following signals heuristically with limitations.
- Use reference overlap only as a labeled heuristic.
- Calculate a normalized weighted score and confidence/capability labels.
- Optional model-assisted evaluation uses a provider boundary, timeout, bounded retries with exponential backoff, schema validation, and deterministic fallback.

### Explainable execution

- Eight stages: validate, persist request, analyze response, scan privacy, score rubric, optional AI evaluation, aggregate, persist report.
- Each stage records pending/running/completed/failed/retrying/recovered/skipped transitions where applicable.
- Events include server timestamp, strict per-run sequence, measured duration, safe message/metadata, and sanitized error data.
- SSE resumes after a supplied event ID and a refresh reconstructs current state from storage.

### Results and history

- Results show overall score, criterion breakdown, evidence, warnings, capability limitations, and timings.
- History lists only records owned by the current session.
- Replay uses persisted events and never changes stored timestamps/durations.
- JSON and Markdown report exports are available client-side from the authorized report payload.

### Reliability and security

- Database writes are transactional; transient operational failures use a small bounded retry.
- Unique ownership/idempotency constraints prevent duplicate records.
- Rate limits, secure validation, safe errors, secret redaction, and same-site HTTP-only cookies are applied.
- Failure injection is enabled only when `APP_ENV=development` and `ENABLE_FAILURE_TESTING=true`.

## User experience requirements

- Responsive dashboard-style application with clear hierarchy, accessible controls, keyboard focus states, and light/dark themes.
- Status is never communicated by color alone.
- On mobile, the execution graph becomes a readable vertical sequence.
- No artificial processing delays; replay may slow visualization independently from recorded timing.

## Success measures

- A valid deterministic evaluation produces a persisted report and at least one terminal event per stage.
- Reopening the browser with the same session displays prior runs.
- An interrupted SSE stream resumes without duplicate or missing persisted events.
- Optional provider failure visibly records retries/recovery and still returns a clearly reduced deterministic report.
- Automated backend and frontend tests cover the mandatory reliability cases.

## Constraints, dependencies, costs, and risks

- Replit Publishing and production databases consume account cloud credits; exact prices and plan entitlements can change and must be checked in the Replit UI before publishing.
- Current Replit guidance exposes database credentials through `DATABASE_URL`; production should use its production database rather than development data.
- Autoscale is suitable because the application is HTTP/SSE driven. SSE connections may reconnect after scale-to-zero or proxy interruption, so clients use event IDs and database restoration.
- Anonymous cookie isolation is appropriate for a public demo, but users lose access if cookies are cleared and it is not enterprise authentication.
- In-memory rate limiting is per instance. A production scale-out requiring strict global quotas should use Redis or a database-backed limiter.
- Model calls may cost money and can disclose submitted content. They are disabled by default and blocked when PII is detected unless explicit server configuration allows sanitized processing.

## Replit research summary (verified 12 November 2026)

- Replit’s current managed database is PostgreSQL-compatible and applications connect with `DATABASE_URL`; current documentation describes a managed database and separates development and production usage.
- Publishing supports Autoscale and Reserved VM deployment types. Autoscale is a good fit for a request-driven web/API workload and supports a `*.replit.app` URL.
- `.replit` supports separate deployment build and run commands. The server must listen on the configured public port and `0.0.0.0`.
- Replit’s public pricing currently shows Starter can publish one public project, while Core adds expanded publishing-related capacity/credits and removes the Replit badge; monitoring documentation identifies Core/Pro/Teams/Enterprise availability for published-app monitoring. Entitlements and costs should be confirmed at publish time.

Sources:

- Replit project configuration: https://docs.replit.com/references/project-setup/configuration
- Replit SQL database: https://docs.replit.com/references/data-and-storage/sql-database
- Replit production databases: https://docs.replit.com/references/data-and-storage/production-databases
- Autoscale deployments: https://docs.replit.com/references/publishing/autoscale-deployments
- Replit pricing: https://replit.com/pricing

## Acceptance criteria

The definition of done in the mission brief is the release gate. A feature is marked verified only after an automated test or a documented manual check demonstrates its behavior. Publishing remains a manual step until a live Replit URL is actually observed.
