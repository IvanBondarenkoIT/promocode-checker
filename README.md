# Promocode Checker

`promocode-checker` is a monorepo for validating unique customer promo codes, closing them at cashier points, reconciling usage against ERP sales, and surfacing admin-level audit and fraud signals.

## Start here for Cursor agents

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/context-handoff.md`](docs/context-handoff.md)
3. [`docs/plan/IMPLEMENTATION_PLAN.md`](docs/plan/IMPLEMENTATION_PLAN.md)
4. [`docs/decisions.md`](docs/decisions.md)
5. [`docs/prompts/`](docs/prompts/)
6. [`docs/reports/`](docs/reports/)

## Project goals

- Fast cashier workflow with an always-focused promo input and scanner-first UX.
- Separate external PostgreSQL database for checker state, logs, admin actions, and analytics.
- ERP reconciliation through Proxy API first, with direct read-only fallback for server deployments.
- Admin and viewer interfaces for visibility, manual correction, reporting, and alert handling.
- Local-first development, Railway demo deployment, and Windows Server Docker production.

## Repository layout

- `backend/` FastAPI backend, domain logic, jobs, and database layer.
- `frontend/` cashier PWA and admin UI.
- `desktop/` lightweight desktop shell for RDP users.
- `infra/` Docker, Compose, and deployment assets.
- `docs/` plan, decisions, prompts, reports, runbooks.
- `config/` business config such as coffee beans group IDs.
- `scripts/` helper scripts for local setup, seed data, and maintenance.
- `tests/` backend and frontend tests.

## Current status

- Stages **1–6** complete (including 5.1 redeem lock).
- Cashier: `http://localhost:5173/?point_id=shop_01`
- Admin: `http://localhost:5173/admin/login` (`.env` `ADMIN_*` / `VIEWER_*`)
- Next: **Stage 7 — Desktop wrapper**

## Continue in a new Cursor chat

```text
Продолжаем promocode-checker.
Этапы 1–6 закрыты. Следующий: Stage 7 Desktop wrapper.
```

## Quick start

1. Create `.env` from `.env.example`.
2. Activate the virtual environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Install backend dependencies:
   - `python -m pip install --upgrade pip`
   - `python -m pip install -e .[dev]`
4. Start local Postgres and apply migrations:
   - `docker compose -f infra/docker-compose.yml up -d`
   - `python scripts/run_migrations.py`
5. (Optional) Seed demo promocodes:
   - `python scripts/seed_promocodes.py`
6. Run the API:
   - `uvicorn app.main:app --app-dir backend --reload`
7. Run cashier PWA:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - open `http://localhost:5173/?point_id=shop_01`
8. Open:
   - Health: `http://localhost:8000/health`
   - Docs: `http://localhost:8000/docs`
