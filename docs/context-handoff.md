# Context Handoff — Promocode Checker

Use this file when opening a new Cursor chat in `D:\CursorProjects\promocode-checker`.

## Paste this into a new chat to continue

```text
Продолжаем promocode-checker.
Сначала прочитай AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/decisions.md, docs/supervisor.md и docs/reports/.
Этапы 1–5 и 5.1 закрыты. Supervisor Stage 5 = PASS.
Следующий этап после OK надзирателя на 5.1: Stage 6 Admin UI (/admin, same Vite app).
Не переспрашивай docs/decisions.md. В конце этапа — commit+push без вопросов.
```

## What already exists

### Stages 1–5 — DONE

- Stage 5 Cashier PWA: PASS (`docs/reports/stage-05-cashier-pwa.md`)

### Stage 5.1 — Concurrent redeem lock — DONE

- FOR UPDATE on redeem + reconcile auto-close
- Report: `docs/reports/stage-05-1-redeem-lock.md`
- Tests: backend **31 passed**

## What is next

### Stage 6 — Admin UI (after supervisor on 5.1)

1. Same Vite app, route `/admin` + login
2. Roles admin/viewer from env
3. Dashboard + tables + audit edits including USED→ACTIVE
4. Report `docs/reports/stage-06-admin-ui.md`

## Locked decisions

See [`docs/decisions.md`](decisions.md). Do not re-ask them.

## Useful commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
python scripts/run_migrations.py
python scripts/seed_promocodes.py
python -m pytest tests/backend -v
uvicorn app.main:app --app-dir backend --reload
cd frontend; npm run dev
# http://localhost:5173/?point_id=shop_01
```
