# Release Test Report

**Date:** 12 November 2026  
**Environment:** Windows local workspace, Python 3.10.11, Node 24.21.0  
**Release candidate:** AI Quality Lab 1.0.0

## Outcome

The locally verifiable release gates pass. No public Replit deployment or Replit production PostgreSQL instance was available in this workspace, so those two checks remain explicitly manual and are not claimed complete.

## Automated checks

| Check | Result | Evidence |
|---|---|---|
| Backend tests | PASS | 16 tests, 87% application statement coverage |
| TypeScript | PASS | `npm run typecheck` |
| Frontend tests | PASS | 5 Vitest replay and workspace-access tests |
| Production bundle | PASS | `npm run build` |
| Dependency audit | PASS | `npm audit`: 0 known vulnerabilities |
| Python compilation | PASS | `python -m compileall app` |

Backend coverage summary: **744 statements, 100 missed, 87%**.

## Backend behaviors verified

- Valid submission creates a persisted report from real input.
- Blank response returns structured 422 field feedback and creates no run.
- Submission content survives processing and is returned only to its owner.
- A second owner cannot access the run or its events (404).
- An explicitly shared workspace key restores the same run on another client, while malformed keys are rejected.
- The same owner/idempotency key returns one original run without re-execution.
- All eight stages appear in the event log.
- Event sequences are increasing and unique within the run.
- SSE resume honors `Last-Event-ID` without replaying older events.
- Completed stage durations are measured, present, and non-negative.
- Dashboard/history restore saved state.
- Potential email and key categories are recorded while raw matched values stay out of event logs.
- Controlled provider timeout produces a retry, then a recovered deterministic fallback and reduced capability statement.
- A controlled final database-write failure preserves the submission and never claims report completion.
- Weighted aggregation honors criterion weights.
- Reference comparison is labeled heuristic with a non-proof limitation.
- Error redaction removes API-key values and database URLs.
- Health reports database connectivity.

## Real-server production smoke test

FastAPI was started with production settings on `127.0.0.1:5010`, serving the compiled `dist/` bundle.

The health, frontend, secure-cookie, and security-header checks were repeated after the final FastAPI/Starlette security-pin upgrade.

| Observation | Result |
|---|---|
| `/api/health` | `200`, `ok`, database `connected` |
| `/` compiled frontend | `200` |
| Real evaluation terminal status | `completed_with_warnings` |
| Persisted weighted score | `76.0` |
| Persisted event count | `23` |
| Event ordering | Strictly ordered |
| Final event | `persist_report / stage.completed` |

The first poll observed the run still in `running`, confirming that the API did not fabricate immediate completion. A later poll observed the persisted terminal state.

## Browser QA

Checked in the in-app browser at 1440×900 and 390×844.

- Dashboard hierarchy, navigation, theme control, metrics, and empty state render correctly.
- New Evaluation form is readable and vertically responsive.
- A real form submission navigated to its saved run and rendered a 71.2/100 report.
- Desktop execution view shows all eight interactive nodes, summaries, statuses, and authentic durations.
- Mobile execution view uses a dedicated vertical eight-stage sequence; labels and durations remain readable.
- Replay mode revealed 0/23 events initially; Play advanced to 4/23 and exposed Pause.
- Result evidence, method labels, privacy status, and limitations rendered.
- Browser console warnings/errors: none.

## Security/dependency audit

The initial complete audit found vulnerabilities in the development test runner only. Vitest was upgraded to 5.1.0; the final production and full audits report zero known vulnerabilities.

## Manual release checks still required

- Publish through the repository owner’s Replit account.
- Confirm a production managed PostgreSQL database is selected and survives republish.
- Verify the public `*.replit.app` URL, HTTPS secure-cookie behavior, scale/reconnect behavior, and deployment monitoring.
- Repeat the incognito isolation and mobile checks on the public URL.
- If an actual provider key is desired, verify one successful model-assisted run and confirm its provider usage fields.

Exact steps are in `docs/DEPLOYMENT.md`.
