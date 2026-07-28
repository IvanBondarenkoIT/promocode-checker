# Stage 02 Data Layer Report

## Planned scope

- create SQLAlchemy models for checker PostgreSQL tables
- add Alembic migration for the initial schema
- implement promocode generation with TTL rules
- add tests for schema and generation logic

## Implementation

- Added enums and models:
  - `promocodes`
  - `checker_logs`
  - `fraud_warnings`
  - `admin_audit_logs`
  - `telegram_notification_logs`
- Added database layer:
  - `backend/app/db/base.py`
  - `backend/app/db/session.py`
- Added Alembic setup:
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/001_initial_schema.py`
- Added promocode generation service:
  - `backend/app/services/promocode_generator.py`
- Added local Postgres compose file:
  - `infra/docker-compose.yml` on port `5433`
- Updated `/health` to report database connectivity status.

## Schema highlights

- `promocodes.promocode` is unique and constrained to exactly 8 digits.
- `checker_logs` stores scan/check/close events with `point_id` and ERP match flag.
- `fraud_warnings` stores suspicious manual-close cases for review.
- `admin_audit_logs` stores manual admin edits with old/new values and reason.
- `telegram_notification_logs` stores alert delivery history and dedup keys.

## Tests

- `python -m ruff check .` -> passed
- first run without Docker: `3 passed, 6 skipped`
- after Docker Postgres on `localhost:5433`:
  - `python scripts/run_migrations.py` -> `001_initial_schema` applied
  - `python -m pytest tests/backend -v` -> `9 passed`

## Review notes

- Stage 2 core deliverables are in place: models, migration, generation service, and test scaffolding.
- Local Postgres via `infra/docker-compose.yml` is verified healthy on port `5433`.
- Alembic migration and all integration tests passed against the live database.

## Risks and follow-ups

- Stage 3 should add API endpoints that use these models and services.
- Consider adding a seed script for demo promocodes in local development.
- Switch Cursor workspace to `D:\CursorProjects\promocode-checker` to avoid confusion with the old typo folder.
