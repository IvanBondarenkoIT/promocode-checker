# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–7 и 5.1/6.1 закрыты. Следующий: Stage 8 Docker / Railway / server-prod.
Desktop: desktop/launch-cashier.ps1 (config.json from config.example.json)
Cashier: http://localhost:5173/?point_id=shop_01
В конце этапа — commit+push без вопросов.
```

## Done

- Stages 1–7, 5.1, 6.1 — see `docs/reports/`

## Next: Stage 8 — Docker / Railway / server-prod

## Commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
uvicorn app.main:app --app-dir backend --reload
cd frontend; npm run dev
```
