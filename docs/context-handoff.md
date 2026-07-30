# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–10 + 11a закрыты (User badge, status hints, dummy barcodes).
Дальше: Stage 11b campaigns + import, затем 11c UI.
Runbooks: docs/runbooks/. CI: .github/workflows/ci.yml.
Прочитай AGENTS.md и docs/context-handoff.md.
```

## Done

- Stages 1–10 — see `docs/reports/`
- Stage 9: GitHub Actions CI + branch→env docs
- Stage 10: runbooks + finalized env matrix + employee cashier guide
- Stage 11a: cashier User badge, status instructions, 20 dummy ACTIVE codes, barcode PNG export (`docs/reports/stage-11a-cashier-user-dummy-barcodes.md`)

## Next (maintenance / follow-ups)

- Stage 11b: campaigns table + CSV wave import
- Stage 11c: show campaign on cashier + admin UI
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
