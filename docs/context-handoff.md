# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–6 и 5.1 закрыты. Следующий: Stage 7 Desktop wrapper.
UI language: English only (cashier/admin/desktop; no i18n).
Admin: http://localhost:5173/admin/login (ADMIN_* / VIEWER_* from .env)
Cashier: http://localhost:5173/?point_id=shop_01
В конце этапа — commit+push без вопросов.
```

## Done

- Stages 1–5, 5.1, 6 — see `docs/reports/`

## Next: Stage 7 — Desktop wrapper

- Lightweight RDP shell, point_id binding, fullscreen-friendly

## Commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
uvicorn app.main:app --app-dir backend --reload
cd frontend; npm run dev
```
