# Replit Deployment Runbook

Verified against current Replit guidance on 12 November 2026. Replit UI labels, quotas, and prices can change; confirm them before publishing.

## Recommended target

Use an **Autoscale** published app. The workload is request-driven HTTP plus reconnectable SSE, and the database-backed stream tolerates instance interruption. A Reserved VM is unnecessary for the challenge demo unless always-on latency is more important than cost.

## 1. Import and database

1. Push this repository to GitHub and import it into Replit, or upload the repository.
2. Open the Replit **Database** tool and add/use the app’s managed PostgreSQL database.
3. Confirm the development environment exposes `DATABASE_URL`. Do not hardcode it.
4. Run the app once and submit a disposable evaluation to create and verify the schema.

Current Replit documentation describes `DATABASE_URL` as the application connection value. Published apps should use their production database, not accidentally share a development database.

## 2. Secrets

Add these in Secrets / Published app secrets:

```text
APP_ENV=production
SESSION_SECRET=<at least 32 random bytes>
DATABASE_URL=<provided by Replit production database flow>
```

Optional:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
PROVIDER_TIMEOUT_SECONDS=8
PROVIDER_MAX_ATTEMPTS=2
ALLOW_EXTERNAL_AI_WITH_PII=false
```

Do not enable `ENABLE_FAILURE_TESTING` in production.

## 3. Build and run settings

The repository contains `.replit` with:

```text
Build: pip install -r requirements.txt && npm ci && npm run build
Run:   python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
Port:  5000 → 80
```

If the Publishing UI overrides `.replit`, enter the same commands there. The deployment is a web server, not a background worker.

## 4. Production database

During Publish/Republish, confirm that Replit creates or selects a **production database**. Copy development data only if it is safe and intentionally intended for the demo. Never seed private prompts or real secrets.

Replit’s database infrastructure and legacy Neon migration rules have changed over time; use the current Database panel and inspect the production `DATABASE_URL` rather than copying an old connection string.

## 5. Verification checklist

After Replit displays the public `*.replit.app` URL:

- [ ] `GET https://<app>.replit.app/api/health` returns `200`, `status: ok`, `database: connected`.
- [ ] Dashboard loads with no console/network errors.
- [ ] Submit a unique prompt/response/rubric and observe all eight stages.
- [ ] Confirm timestamps and durations vary with real work and are not example constants.
- [ ] Refresh the run page and confirm state/events restore.
- [ ] Replay; pause, restart, and change speed.
- [ ] Open a private/incognito browser and confirm the first session’s run URL returns Not Found.
- [ ] Submit an invalid response and confirm field feedback without cleared input.
- [ ] If an AI key is configured, test a non-sensitive input; confirm model usage/capability labels.
- [ ] Test a PII-like input and confirm the external AI stage is skipped by the privacy gate.
- [ ] Inspect logs for secrets or raw prompt content; none should appear.
- [ ] Test a 390 px mobile viewport and a desktop viewport.

Only after these pass should the public URL be added to the Handshake submission.

## Costs and plans

Replit Publishing and production database compute/storage use account credits. The public pricing page at research time showed a Starter public-project allowance and Core/Pro monthly credits; published-app monitoring documentation listed Core and higher tiers. Confirm the selected deployment’s estimated monthly cost and current entitlement in the Publishing UI. Configure a usage budget.

## Rollback

1. Keep the last known-good Git commit/tag.
2. Use Replit Republish with that snapshot if application code regresses.
3. Use database rollback only according to the plan’s available retention and after confirming the correct development/production database.
4. Never “fix” a database incident by pointing production at the development URL.

## Official references

- https://docs.replit.com/references/project-setup/configuration
- https://docs.replit.com/references/data-and-storage/sql-database
- https://docs.replit.com/references/data-and-storage/production-databases
- https://docs.replit.com/references/publishing/autoscale-deployments
- https://docs.replit.com/references/publishing/monitoring-a-deployment
- https://replit.com/pricing
