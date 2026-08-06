# Local Development

Operational runbooks (local / server-prod / employees): [`runbooks/`](runbooks/README.md).

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

Optional seed for cashier testing:

```powershell
python scripts/seed_promocodes.py
```

Dummy codes (fixed, idempotent — safe to re-run):

| Code | Expected result |
|------|-----------------|
| `10000001`–`10000020` | ACTIVE |
| `20000001`–`20000002` | USED |
| `30000001`–`30000002` | EXPIRED |
| `99999999` | NOT_FOUND (not in DB) |

### Troubleshooting

**Admin/cashier API returns 500, logs show `relation "promocodes" does not exist`:**

The DB was stamped by Alembic but tables were never created. Re-apply schema:

```powershell
python scripts/run_migrations.py
python scripts/seed_promocodes.py
```

`run_migrations.py` auto-detects this broken state and re-applies the migration.

**Vite proxy errors (`ECONNREFUSED 127.0.0.1:8000`):**

Start the backend before using the UI:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

Cashier API examples:

```powershell
# check
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/cashier/check -ContentType "application/json" -Body '{"code":"12345678"}'

# redeem
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/cashier/redeem -ContentType "application/json" -Body '{"code":"12345678","point_id":"shop_01"}'

# barcode PNG
Invoke-WebRequest -Uri http://localhost:8000/api/v1/cashier/barcode/12345678 -OutFile promo.png
```

## Cashier PWA (Stage 5)

In a second terminal:

```powershell
cd D:\CursorProjects\promocode-checker\frontend
npm install
npm run dev
```

Open `http://localhost:5173/?point_id=shop_01` (cashier) or `http://localhost:5173/admin/login` (admin; creds from `.env` `ADMIN_*` / `VIEWER_*`).

Frontend tests:

```powershell
npm test
```

If npm SSL fails on this machine, use `npm install --strict-ssl=false` (same class of issue as pip `--trusted-host`).

## Docker full stack (Stage 8)

Single container serves API + built cashier/admin UI:

```powershell
docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build
```

- Cashier: `http://localhost:8000/?point_id=shop_01`
- Admin: `http://localhost:8000/admin/login`
- Health: `http://localhost:8000/health`

Production: see [`docs/reports/stage-08-deploy.md`](reports/stage-08-deploy.md) and [`env-matrix.md`](env-matrix.md). General smoke: [`runbooks/server-prod.md`](runbooks/server-prod.md).

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

## Stage 3 scope

- Cashier endpoints: `POST /api/v1/cashier/check`, `POST /api/v1/cashier/redeem`, `GET /api/v1/cashier/barcode/{code}`
- `checker_logs` for `SCAN_CHECK` / `MANUAL_CLOSE`
- seed script `scripts/seed_promocodes.py`
- API tests for payloads and log creation

Stages 1–5 are closed in code. Next: Admin UI (Stage 6) after supervisor check on Stage 5.

```powershell
python scripts/run_reconcile.py
```
