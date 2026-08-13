# Context Handoff — Promocode Checker

## Paste into new chat

```text
Продолжаем promocode-checker.
Этапы 1–10 + 11a–11d + Stage 4.1 + gap checklist + Stage T–Z закрыты.
Railway убран: только local + server-prod.
Кампании делятся на TEST/LIVE, глобальный переключатель в админке.
Промокод сегмента = номер карты лояльности (8–20 цифр); поле promocode отдельное.
Режим закрытия: PROMO_ENFORCEMENT_MODE=monitor|enforce; порог 2 кг в одном чеке.
Server ERP: direct Firebird OK (3050 + C:/db/GEORGIA.GDB). Stage AA: admin card forms.
Next: LIVE + monitor alerts, then enforce.
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
- Stage T: Telegram subscribe bot + human RU alerts + `/demo` calibration (`docs/reports/stage-t-telegram-ops.md`)
- Drop Railway (2026-08-04): local + server-prod only (`docs/reports/drop-railway-2026-08-04.md`)
- Stage U: daily digests 10:00/22:00 + alert modes full/digest (`docs/reports/stage-u-telegram-daily.md`)
- Stage V: segment import + TEST/LIVE scope + admin scope switch (`docs/reports/stage-v-preprod-segment.md`)
- Stage W: promocode = loyalty card, length 8–20, remap script (`docs/reports/stage-w-card-as-promocode.md`)
- Stage X: monitor/enforce modes + 2 kg per order (`docs/reports/stage-x-monitor-mode.md`)
- Stage Y: shop ORGN monitor calibration (`docs/reports/stage-y-shop-monitor-calibration.md`)
- Stage Z: direct Firebird ERP on server + probe CLI; **server probe PASS 2026-08-13** (`docs/reports/stage-z-direct-firebird.md`)
- Stage AA: admin customer card list + element forms (`docs/reports/stage-aa-admin-card-forms.md`)

## Next (launch preparation)

- Scope **LIVE** + keep `PROMO_ENFORCEMENT_MODE=monitor`; verify `sale_observations` + Telegram on real coffee sales
- Owner switch to `enforce` only after monitor alerts look correct
- Decide how issued codes reach customers (export CSV is ready)
- Owner decision: auto-close when the customer never showed the code
- Run **general smoke / regression** on server — [runbooks/server-prod.md](runbooks/server-prod.md)
- Optional TLS / reverse proxy, GHCR image publish
- Merge Stage AA to `main` after local admin card UI PASS

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
