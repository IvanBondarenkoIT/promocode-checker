# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–10 закрыты (план реализации выполнен).
Runbooks: docs/runbooks/ (local / railway / server-prod / employee-cashier).
CI: .github/workflows/ci.yml. Env: docs/env-matrix.md.
Прочитай AGENTS.md и docs/context-handoff.md.
```

## Done

- Stages 1–10 — see `docs/reports/`
- Stage 9: GitHub Actions CI + branch→env docs
- Stage 10: runbooks + finalized env matrix + employee cashier guide

## Next (maintenance / follow-ups)

- Stage 4.1 live Granit SQL validation (deferred)
- Optional TLS / reverse proxy on server-prod
- Optional GHCR image publish
- Confirm Railway project connected to `railway-demo`

## Commands

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
docker compose -f infra/docker-compose.yml up -d
uvicorn app.main:app --app-dir backend --reload
cd frontend; npm run dev
```

Full stack:

```powershell
docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build
```
