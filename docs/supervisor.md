# Supervisor Role

This chat (`promocode-chacker` workspace conversation) acts as the **external supervisor** for `D:\CursorProjects\promocode-checker`.

## How to use

After each stage in the implementation agent, paste:

```text
Надзиратель: проверь Stage N.
Сверь docs/reports/stage-0N-*.md, код и docs/plan/IMPLEMENTATION_PLAN.md + docs/decisions.md.
Проверь, что продуктовый UI на английском (English only, без i18n).
Дай вердикт PASS / PARTIAL / FAIL, отклонения, блокеры до следующего этапа.
```

## Supervisor checklist

1. Stage report exists and has: scope / implementation / tests / review / risks
2. Plan checklist matches reality
3. Locked decisions not violated (incl. **English-only product UI**)
4. Tests claimed in report are plausible / re-runnable
5. Open questions listed before next stage
6. Docs not stale (AGENTS / handoff / README / plan agree)

## Audits

- 2026-07-28 Stages 1–4: [`docs/reports/supervisor-audit-2026-07-28.md`](reports/supervisor-audit-2026-07-28.md)
- 2026-07-28 Stage 5 gate: [`docs/reports/supervisor-gate-stage5-2026-07-28.md`](reports/supervisor-gate-stage5-2026-07-28.md)
- 2026-07-28 Stage 5 close: [`docs/reports/supervisor-audit-stage5-2026-07-28.md`](reports/supervisor-audit-stage5-2026-07-28.md) — **PASS**

## Current green light

- Stages 1–8: closed
- **Next: Stage 9 CI/CD**
