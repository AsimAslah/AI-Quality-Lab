# Pull Request: Build AI Quality Lab explainable evaluation platform

## Summary

- Adds a complete React/FastAPI response-evaluation application.
- Persists ownership-scoped runs, reports, and ordered execution events.
- Adds an eight-stage live SSE/React Flow execution diagram and accurate replay.
- Adds deterministic/heuristic rubric evaluation, PII scanning, optional provider retries/fallback, idempotency, rate limiting, and redaction.
- Adds responsive light/dark UI, export, history, Replit configuration, and full product/deployment documentation.

## Verification

- `python -m pytest -q`
- `npm run typecheck`
- `npm run test`
- `npm run build`
- `npm audit`
- production server health/submission/restore smoke test

## Manual release step

Publishing requires the repository owner’s Replit account and production database selection. Add the verified public URL only after completing `docs/DEPLOYMENT.md`.
