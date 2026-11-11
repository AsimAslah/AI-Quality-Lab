# Database Schema

## `evaluation_runs`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID/string(36) | Primary key |
| `owner_hash` | string(64) | Indexed HMAC of owner cookie; authorization boundary |
| `idempotency_key` | string(64) | Unique with owner |
| `title` | string(160) | Safe display title |
| `status` | string(32) | queued, running, completed, completed_with_warnings, failed |
| `prompt` | text | Authorized raw prompt |
| `response` | text | Authorized raw response under evaluation |
| `reference` | text nullable | Optional authorized context/reference |
| `rubric` | JSON | Validated criterion definitions |
| `preferences` | JSON | Model-evaluation and privacy preferences |
| `report` | JSON nullable | Final normalized report |
| `warning_count` | integer | Summary projection |
| `overall_score` | float nullable | Summary projection, 0–100 |
| `current_stage` | string nullable | Fast current-state lookup |
| `error_code` | string nullable | Sanitized terminal error category |
| `created_at` | timestamp tz | Server timestamp |
| `updated_at` | timestamp tz | Server timestamp |
| `completed_at` | timestamp tz nullable | Terminal timestamp |

Indexes/constraints:

- unique `(owner_hash, idempotency_key)`
- index `(owner_hash, created_at)`
- index `status`

## `execution_events`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID/string(36) | Primary key |
| `run_id` | FK | Cascade delete with run |
| `sequence` | integer | Strict order within run |
| `stage_id` | string(48) | Stable pipeline stage key |
| `event_type` | string(64) | e.g. `stage.started`, `provider.retrying` |
| `status` | string(24) | pending/running/completed/failed/retrying/recovered/skipped |
| `occurred_at` | timestamp tz | Server wall-clock timestamp |
| `duration_ms` | float nullable | Measured with monotonic clock |
| `message` | string(300) | Human-readable, redacted summary |
| `metadata_json` | JSON | Allowlisted safe data only |
| `error_code` | string(64) nullable | Sanitized class/category |
| `error_message` | string(300) nullable | Redacted user-safe error |

Indexes/constraints:

- unique `(run_id, sequence)`
- index `(run_id, occurred_at)`
- foreign key to `evaluation_runs.id`

## Migration and portability

SQLAlchemy’s generic JSON and timezone-aware timestamp types support PostgreSQL and SQLite. PostgreSQL is required for the deployed persistent environment. SQLite at `./data/ai_quality_lab.db` is a documented local fallback, not the deployment persistence strategy.

Future migrations should add a user/account table and replace `owner_hash` with a foreign key while retaining existing runs through an ownership migration.
