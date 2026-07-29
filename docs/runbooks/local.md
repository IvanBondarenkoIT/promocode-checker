# Runbook — Local

For developers on Windows. Full setup details: [`../local-development.md`](../local-development.md).

**UI language:** English only.

## Options

### A) Split (dev)

1. Postgres: `docker compose -f infra/docker-compose.yml up -d`
2. Copy `.env.example` → `.env`, activate `.venv`
3. Migrations: `python scripts/run_migrations.py`
4. Optional seed: `python scripts/seed_promocodes.py`
5. Backend: `uvicorn app.main:app --app-dir backend --reload`
6. Frontend: `cd frontend; npm install; npm run dev`
7. Open:
   - Cashier: `http://localhost:5173/?point_id=shop_01`
   - Admin: `http://localhost:5173/admin/login`
   - Health: `http://localhost:8000/health` → expect `"status":"ok"`, `"database":"ok"`, `"schema":"ok"`

If `STATIC_DIR` is empty and `frontend/dist` exists, the API can also serve the built UI on `:8000` after `npm run build`.

### B) Full Docker stack

```powershell
docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build
```

- Cashier: `http://localhost:8000/?point_id=shop_01`
- Admin: `http://localhost:8000/admin/login`
- Health: `http://localhost:8000/health`

Seed is on by default via `AUTO_SEED_PROMOCODES=1` in the app compose overlay.

## Dummy promocodes

| Code | Expected |
|------|----------|
| `10000001`–`10000003` | ACTIVE |
| `20000001`–`20000002` | USED |
| `30000001`–`30000002` | EXPIRED |
| `99999999` | NOT FOUND |

## Admin / viewer

Credentials from `.env`: `ADMIN_*`, `VIEWER_*`.

## Reconcile (manual)

```powershell
python scripts/run_reconcile.py
```

Local ERP mode: prefer `ERP_ACCESS_MODE=mock` in `.env`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `relation "promocodes" does not exist` / Ready lamp **DB not initialized** | `python scripts/run_migrations.py` then seed |
| Cashier/admin 404 on `:8000` | Build frontend (`cd frontend; npm run build`) or use Vite `:5173`; restart uvicorn |
| Vite proxy `ECONNREFUSED :8000` | Start backend first |
| Ready lamp green but check fails | Health must include `"schema":"ok"`; re-run migrations |
| npm SSL errors | `npm install --strict-ssl=false` |

## CI note

GitHub Actions runs on `develop` (see [`../branching.md`](../branching.md)). Local Docker Desktop is optional for day-to-day; CI uses a Postgres service.
