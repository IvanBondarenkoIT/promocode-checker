# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–10 + 11a–11d + Stage 4.1 ERP probe закрыты.
Probe: docs/runbooks/erp-probe.md — owner visual OK CSV before reconcile live demo.
Прочитай AGENTS.md и docs/context-handoff.md.
```

## Done

- Stages 1–10 — see `docs/reports/`
- Stage 9: GitHub Actions CI + branch→env docs
- Stage 10: runbooks + finalized env matrix + employee cashier guide
- Stage 11a: cashier User badge, status instructions, 20 dummy ACTIVE codes, barcode PNG export (`docs/reports/stage-11a-cashier-user-dummy-barcodes.md`)
- Stage 11b: campaigns schema + CSV import (`docs/reports/stage-11b-campaigns-import.md`)
- Stage 11c: campaign display on cashier + admin (`docs/reports/stage-11c-campaign-ui.md`)
- Stage 11d: DEMO_LOCAL seed + server rollout checklist (`docs/reports/stage-11d-server-rollout.md`)
- Stage 4.1: Granit coffee SQL + shop cards + probe CLI (`docs/reports/stage-41-erp-probe.md`)

## Next (maintenance / follow-ups)

- Owner visual OK of live proxy probe CSV (`artifacts/erp-probe/`)
- After OK: optional AUTO_CLOSE demo with seeded ACTIVE codes for shop cards that sold coffee
- Apply Stage 11d on Windows Server (pull / rebuild / seed) if not done
- Real campaign CSV import on server-prod
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
