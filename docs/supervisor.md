# Supervisor Role

This chat acts as the **external supervisor** for `D:\CursorProjects\promocode-checker`.

## How to use

```text
Надзиратель: проверь Stage N.
Сверь docs/reports/stage-0N-*.md, код и docs/plan/IMPLEMENTATION_PLAN.md + docs/decisions.md.
Проверь, что продуктовый UI на английском (English only, без i18n).
Дай вердикт PASS / PARTIAL / FAIL, отклонения, блокеры до следующего этапа.
```

## Current green light

- Stages 1–10 + 11a–11d + Stage 4.1: closed
- Gap checklist 2026-08-04: closed in repo (`docs/reports/gap-checklist-2026-08-04.md`)
- **Next (owner ops):** Telegram + ERP env on server-prod; `desktop/update-prod.ps1`; optional Railway/TLS/GHCR

## Audits / reports

See `docs/reports/` including `stage-09-cicd.md`, `stage-10-runbooks.md`, `stage-41-erp-probe.md`, `gap-checklist-2026-08-04.md`.
