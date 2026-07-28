# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–8 закрыты. Следующий: Stage 9 CI/CD.
Docker stack: docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build
```

## Done

- Stages 1–8 — see `docs/reports/`

## Next: Stage 9 — CI/CD

## Commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
uvicorn app.main:app --app-dir backend --reload
cd frontend; npm run dev
```
