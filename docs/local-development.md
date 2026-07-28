# Local Development

## Requirements

- Python `3.11+`
- PostgreSQL `15+`
- Node.js `20+`
- PowerShell on Windows

## Initial setup

1. Copy `.env.example` to `.env`.
2. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install backend dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

If pip fails with SSL/certificate errors on Windows, retry with trusted hosts:

```powershell
python -m pip install -e .[dev] --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

4. Prepare a local PostgreSQL database:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker
```

Optional local Postgres via Docker:

```powershell
docker compose -f infra/docker-compose.yml up -d
python scripts/run_migrations.py
```

5. Start the backend:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

6. Verify the service:

```text
GET /health
```

## Stage 1 scope

At this stage the repository contains:

- Python environment bootstrap
- FastAPI health endpoint
- env template
- base folder structure
- branching and stage-report documentation

## Stage 2 scope

- SQLAlchemy models for `promocodes`, `checker_logs`, `fraud_warnings`, `admin_audit_logs`, `telegram_notification_logs`
- Alembic migration `001_initial_schema`
- promocode generation service with TTL support
- local Postgres compose file on port `5433`
- backend tests for models and promocode generation

Stages 1–2 are closed in code. Next: cashier API (`check` / `redeem` / barcode) in Stage 3, then frontend PWA, ERP connectors, admin UI, and production Docker/Railway assets.
