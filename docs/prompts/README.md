# Prompts Index

Use these prompts when starting or reviewing work in Cursor.

| File | Purpose |
|------|---------|
| [`project-prompts.md`](project-prompts.md) | Main reusable prompts: continue, architecture, review, antifraud, UX, deploy |
| [`stage-prompts.md`](stage-prompts.md) | Ready-to-paste prompts for stages 3–10 **with mandatory stage-gate on every stage** |

## Stage-gate (always)

Every stage must end with:

1. tests / verification
2. short review
3. `docs/reports/stage-XX-....md`
4. status updates (`AGENTS.md`, handoff, plan, INDEX, stage-prompts)
5. short доклад: done / tests / gaps / open questions
6. next stage only after explicit OK

This is duplicated inside each stage block in [`stage-prompts.md`](stage-prompts.md) so agents cannot skip it when pasting a single stage prompt.

Also read:

- [`../context-handoff.md`](../context-handoff.md)
- [`../plan/IMPLEMENTATION_PLAN.md`](../plan/IMPLEMENTATION_PLAN.md)
- [`../decisions.md`](../decisions.md)
