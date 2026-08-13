# Stage Work Prompt Pack

## UI language (locked — every stage with UI)

All user-facing UI strings — cashier, admin, desktop — **English only**. No i18n, no Russian labels in the product. Dates/times: `en-US`. See [`docs/decisions.md`](../decisions.md).

## Mandatory stage-gate (include in EVERY stage)

Every stage prompt below already embeds this. Do not drop it when pasting:

```text
STAGE-GATE (обязательно на каждом этапе):
1. Реализуй ТОЛЬКО текущий этап — не начинай следующий.
2. UI: только английский (English) во всём продуктовом интерфейсе — без i18n и без русских подписей.
3. Напиши/обнови тесты для этапа.
4. Прогони проверки (ruff + pytest / ручные checks по этапу).
5. Сделай короткое ревью результата.
6. Создай/обнови docs/reports/stage-XX-....md (scope / impl / tests / risks / open questions).
7. Обнови статусы: AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/INDEX.md, docs/prompts/stage-prompts.md.
8. В конце чата дай короткий доклад:
   - что сделано
   - какие тесты / проверки
   - что могли упустить
   - какие вопросы нужно уточнить ДО следующего этапа
9. В конце этапа: commit + push на feature/*, merge в develop, push develop (не спрашивать владельца).
10. Не начинай следующий этап без явного OK пользователя / надзирателя.
```

Also reuse the pack in [`project-prompts.md`](project-prompts.md) sections `0`, `2`, `3`.

---

## Stage 3 — Backend API — DONE

Already delivered as cashier API:

- `POST /api/v1/cashier/check`
- `POST /api/v1/cashier/redeem`
- `GET /api/v1/cashier/barcode/{code}`
- report: `docs/reports/stage-03-cashier-api.md`

## Stage 4 — ERP reconcile — DONE

Already delivered:

- ERP adapter mock/proxy/direct + reconcile CLI
- AUTO_CLOSE, fraud warnings, Telegram dedup
- report: `docs/reports/stage-04-erp-reconcile.md`
- tests: 28 passed

## Stage 5 — Cashier PWA — DONE (supervisor PASS)

Already delivered:

- Vite/React cashier PWA + heartbeat endpoint
- report: `docs/reports/stage-05-cashier-pwa.md`
- supervisor: `docs/reports/supervisor-audit-stage5-2026-07-28.md` — PASS
- tests: backend 29 passed, frontend 8 passed

## Stage 5.1 — Concurrent redeem lock — DONE

Already delivered:

- FOR UPDATE on redeem + reconcile auto-close
- report: `docs/reports/stage-05-1-redeem-lock.md`
- tests: backend 31 passed

- [`reports/stage-06-admin-ui.md`](reports/stage-06-admin-ui.md)

## Stage 6 — Admin UI — DONE

Report: [`reports/stage-06-admin-ui.md`](reports/stage-06-admin-ui.md)

## Stage 6.1 — Cashier polish — DONE

- English cashier UI, ready lamp, status/redeem UX
- Dummy seed codes, migration auto-recovery
- Report: [`reports/stage-06-1-cashier-polish.md`](reports/stage-06-1-cashier-polish.md)

## Stage 7 — Desktop wrapper — DONE

Report: [`reports/stage-07-desktop-wrapper.md`](reports/stage-07-desktop-wrapper.md)

## Stage 8 — Deploy — DONE

Report: [`reports/stage-08-deploy.md`](reports/stage-08-deploy.md)

## Stage 9 — CI/CD — NEXT

## Stage 9 — CI/CD — DONE

Already delivered:

- `.github/workflows/ci.yml` — ruff + pytest (Postgres service) + frontend test/build
- `docs/branching.md` — branch→env mapping
- report: `docs/reports/stage-09-cicd.md`

## Stage 10 — Runbooks polish — DONE

Already delivered:

- `docs/runbooks/` — local, server-prod, employee-cashier
- `docs/env-matrix.md` finalized
- report: `docs/reports/stage-10-runbooks.md`

Implementation plan stages **1–10 complete**. Further work is maintenance / deferred follow-ups. Railway dropped — acceptance on server-prod.

## Stage AC — Reconcile cursor — DONE

Already delivered:

- `reconcile_state` cursor + `RECONCILE_OVERLAP_HOURS=48`
- poll every 10 minutes on prod
- same-calendar-day ERP sales count
- report: `docs/reports/stage-ac-reconcile-cursor.md`

## Stage AD — Telegram topics + code lookup — DONE

Already delivered:

- six alert topics + mandatory `system`
- persistent keyboard + inline toggles
- read-only promocode status from chat
- report: `docs/reports/stage-ad-telegram-topics.md`

## Stage AE — Telegram subscriber join alert + list UI — DONE

Already delivered:

- `subscriber_joined` → `system` (exclude joining chat)
- profile columns username/display_name (migration `010`)
- button «Подписчики» + `/subscribers`
- report: `docs/reports/stage-ae-telegram-subscribers-ui.md`

