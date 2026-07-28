# Context Handoff — Promocode Checker

Use this file when opening a new Cursor chat in `D:\CursorProjects\promocode-checker`.

## Paste this into a new chat to continue

```text
Продолжаем promocode-checker.
Сначала прочитай AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/decisions.md и последние docs/reports/.
Этапы 1–4 закрыты. Docker Postgres на 5433, cashier API + ERP reconcile/Telegram готовы (28 tests passed).
Следующий этап: Stage 5 — Cashier PWA, с тестами, ревью и stage-report перед этапом 6.
Не переспрашивай решения из docs/decisions.md.
```


## What already exists

### Stage 1 — Bootstrap — DONE

- Correct project folder: `promocode-checker`
- Git repo, Python 3.11 `.venv`, FastAPI `/health`
- Docs for branching, local development, testing stages

### Stage 2 — Data layer — DONE

- Models: `promocodes`, `checker_logs`, `fraud_warnings`, `admin_audit_logs`, `telegram_notification_logs`
- Alembic migration `001_initial_schema`
- Promocode generator with 8-digit uniqueness and TTL
- Local compose Postgres on `localhost:5433`

### Stage 3 — Cashier API — DONE

- `POST /api/v1/cashier/check`
- `POST /api/v1/cashier/redeem`
- `GET /api/v1/cashier/barcode/{code}` → PNG Code128
- Services: `cashier.py`, `barcode.py`, `promocode_generator.py`
- Seed script: `scripts/seed_promocodes.py`
- Report: `docs/reports/stage-03-cashier-api.md`
- Tests: included in current **28 passed** suite

### Stage 4 — ERP reconcile + Telegram — DONE

- ERP adapter: mock / proxy / direct (+ proxy→direct fallback)
- Reconcile job: `scripts/run_reconcile.py` + `backend/app/jobs/reconcile.py`
- AUTO_CLOSE + fraud warnings + Telegram dedup
- Report: `docs/reports/stage-04-erp-reconcile.md`
- Tests: **28 passed**

## What is next

### Stage 5 — Cashier PWA

Must implement:

1. One numeric input, length 8
2. Absolute autofocus recovery
3. Scanner Enter auto-submit + 1.5s debounce
4. Status colors + Redeem button + audio feedback
5. `point_id` from query/settings + heartbeat without login
6. Tests/manual scanner checks + `docs/reports/stage-05-cashier-pwa.md`

## Locked decisions

See [`docs/decisions.md`](decisions.md). Do not re-ask them.

## Known caveats

- Old empty typo folder `promocode-chacker` may still exist; ignore/delete after switching workspace.
- Concurrent redeem race is not locked yet (noted in stage 3 report).
- PyPI install may need `--trusted-host` on this Windows machine.
- Docker Desktop must be running for local Postgres tests.

## Useful commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
python scripts/run_migrations.py
python scripts/seed_promocodes.py
python scripts/run_reconcile.py
python -m pytest tests/backend -v
uvicorn app.main:app --app-dir backend --reload
```
