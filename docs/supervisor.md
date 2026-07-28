# Supervisor Role

This chat (`promocode-chacker` workspace conversation) acts as the **external supervisor** for `D:\CursorProjects\promocode-checker`.

## How to use

After each stage in the implementation agent, paste:

```text
Надзиратель: проверь Stage N.
Сверь docs/reports/stage-0N-*.md, код и docs/plan/IMPLEMENTATION_PLAN.md + docs/decisions.md.
Дай вердикт PASS / PARTIAL / FAIL, отклонения, блокеры до следующего этапа.
```

## Supervisor checklist

1. Stage report exists and has: scope / implementation / tests / review / risks
2. Plan checklist matches reality
3. Locked decisions not violated
4. Tests claimed in report are plausible / re-runnable
5. Open questions listed before next stage
6. Docs not stale (AGENTS / handoff / README / plan agree)

## Last audit

- Date: 2026-07-28
- Scope: Stages 1–4
- Result: see `docs/reports/supervisor-audit-2026-07-28.md`
