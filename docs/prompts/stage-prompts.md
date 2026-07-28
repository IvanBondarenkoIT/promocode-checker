# Stage Work Prompt Pack

## Mandatory stage-gate (include in EVERY stage)

Every stage prompt below already embeds this. Do not drop it when pasting:

```text
STAGE-GATE (обязательно на каждом этапе):
1. Реализуй ТОЛЬКО текущий этап — не начинай следующий.
2. Напиши/обнови тесты для этапа.
3. Прогони проверки (ruff + pytest / ручные checks по этапу).
4. Сделай короткое ревью результата.
5. Создай/обнови docs/reports/stage-XX-....md (scope / impl / tests / risks / open questions).
6. Обнови статусы: AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/INDEX.md, docs/prompts/stage-prompts.md.
7. В конце чата дай короткий доклад:
   - что сделано
   - какие тесты / проверки
   - что могли упустить
   - какие вопросы нужно уточнить ДО следующего этапа
8. Коммиты/push — только если пользователь явно попросил.
9. Не начинай следующий этап без явного OK пользователя.
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

## Stage 5 — Cashier PWA — NEXT

```text
Этап 5: cashier PWA.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-04-erp-reconcile.md.
Must-have: absolute autofocus, numeric 8 digits, scanner Enter, 1.5s debounce, status colors, audio feedback, point_id.
No cashier login. Session heartbeat only.
Не начинай Admin UI / desktop / deploy.

STAGE-GATE (обязательно):
- тесты/ручная проверка сканера
- ревью
- docs/reports/stage-05-cashier-pwa.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / вопросы до Stage 6
- коммиты только по явной просьбе
- следующий этап только после OK
```

## Stage 6 — Admin UI

```text
Этап 6: admin UI.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-05-cashier-pwa.md.
Roles admin/viewer from env.
Dashboard + all tables + logs + fraud + reconcile health.
Admin full edits including USED→ACTIVE with audit reason.
Viewer read-only.
Не начинай desktop / deploy.

STAGE-GATE (обязательно):
- тесты (admin vs viewer, audit trail)
- ревью
- docs/reports/stage-06-admin-ui.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / вопросы до Stage 7
- коммиты только по явной просьбе
- следующий этап только после OK
```

## Stage 7 — Desktop shell

```text
Этап 7: desktop wrapper for RDP cashiers.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-06-admin-ui.md.
Lightweight app-like launch, point_id binding, fullscreen-friendly.
Не начинай Docker/Railway/CI.

STAGE-GATE (обязательно):
- тесты/ручная проверка под RDP
- ревью
- docs/reports/stage-07-desktop-wrapper.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / вопросы до Stage 8
- коммиты только по явной просьбе
- следующий этап только после OK
```

## Stage 8 — Deploy

```text
Этап 8: Docker local/prod + Railway demo.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-07-desktop-wrapper.md.
Reuse patterns from dimkava-big-book / prices-monitoring-scrappers / stock-safety-monitor.
Healthchecks + crash alerts + reconcile cron wiring.
Не начинай полный CI/CD polish без необходимости.

STAGE-GATE (обязательно):
- build/smoke checks local (+ Railway config review)
- ревью
- docs/reports/stage-08-deploy.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / вопросы до Stage 9
- коммиты только по явной просьбе
- следующий этап только после OK
```

## Stage 9 — CI/CD

```text
Этап 9: GitHub Actions + branch→env mapping.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-08-deploy.md.
develop / railway-demo / main.
Не расползаться на новые фичи.

STAGE-GATE (обязательно):
- проверить CI на PR/ветках
- ревью
- docs/reports/stage-09-cicd.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / вопросы до Stage 10 (runbooks)
- коммиты только по явной просьбе
- следующий этап только после OK
```

## Stage 10 — Runbooks polish

```text
Этап 10: runbooks polish.
Сначала прочитай AGENTS.md, docs/decisions.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/reports/stage-09-cicd.md.
local / railway / server docs complete, env matrix finalized, employee launch instructions.

STAGE-GATE (обязательно):
- проверка ссылок/инструкций
- ревью
- docs/reports/stage-10-runbooks.md
- обновить AGENTS.md + context-handoff + IMPLEMENTATION_PLAN + INDEX + этот файл
- короткий доклад: сделано / проверки / упущения / открытые вопросы
- коммиты только по явной просьбе
```
