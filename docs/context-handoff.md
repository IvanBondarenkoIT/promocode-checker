# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–9 закрыты. Следующий: Stage 10 Runbooks polish.
CI: .github/workflows/ci.yml (ruff + pytest+Postgres + frontend test/build).
Прочитай AGENTS.md, docs/branching.md, docs/reports/stage-09-cicd.md.
```

## Done

- Stages 1–9 — see `docs/reports/`
- Stage 9: GitHub Actions CI + branch→env docs

## Next: Stage 10 — Runbooks polish

- local / railway / server docs complete
- env matrix finalized
- employee launch instructions

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
