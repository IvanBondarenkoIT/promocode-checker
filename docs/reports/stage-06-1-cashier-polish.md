# Stage 06.1 — Cashier polish, seed, migrations fix

## Scope

Post–Stage 6 UX and local-dev fixes before desktop wrapper.

## Implementation

- Cashier UI: simplified top bar (Shop + ready lamp), status panel above input, non-button status styling, prominent redeem CTA when ACTIVE
- English-only cashier labels (`logic.ts`, `CashierApp.tsx`, `index.html`)
- Ready indicator via `/health` + heartbeat
- Dummy seed promocodes (`scripts/seed_promocodes.py`) — fixed codes for ACTIVE/USED/EXPIRED/NOT_FOUND
- `scripts/run_migrations.py` auto-recovery when Alembic stamp exists without tables
- Admin API client: parse FastAPI `detail` errors
- Docs: English-only UI locked in prompts/decisions; local-dev troubleshooting + dummy code table

## Tests

- Backend: **36 passed**
- Frontend: **10 passed**

## Risks / follow-ups

1. Ready lamp reflects API reachability, not Postgres schema health (check/redeem failures still show in status).
2. Stage 7 desktop wrapper next.
