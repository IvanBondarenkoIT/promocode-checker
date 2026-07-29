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

- Stages 1–10: closed (implementation plan complete)
- **Next:** maintenance / deferred follow-ups (Stage 4.1 live Granit SQL, TLS, optional GHCR)

## Audits / reports

See `docs/reports/` including `stage-09-cicd.md`, `stage-10-runbooks.md`.
