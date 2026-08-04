# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–10 + 11a–11d + Stage 4.1 + gap checklist 2026-08-04 закрыты.
Owner ops: Telegram + ERP на server-prod; desktop/update-prod.ps1.
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
- Stage 4.1: Granit coffee SQL + shop cards + probe CLI + live AUTO_CLOSE demo (`docs/reports/stage-41-erp-probe.md`)
- Gap checklist: TG summary + ops runbook + fdb/proxy notes + update-prod (`docs/reports/gap-checklist-2026-08-04.md`)

## Next (maintenance / follow-ups)

- Server-prod: fill Telegram + confirm ERP mode; `desktop\update-prod.ps1`
- Real campaign CSV import on server-prod when marketing ready
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
