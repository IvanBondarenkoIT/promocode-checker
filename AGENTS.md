# AGENTS.md — Promocode Checker

This file is the primary handoff for any Cursor agent working in this repository.

## Read first

1. [`docs/context-handoff.md`](docs/context-handoff.md) — current status and how to continue
2. [`docs/plan/IMPLEMENTATION_PLAN.md`](docs/plan/IMPLEMENTATION_PLAN.md) — full implementation plan
3. [`docs/decisions.md`](docs/decisions.md) — locked product and technical decisions
4. [`docs/business-requirements.md`](docs/business-requirements.md) — original business flow
5. [`docs/prompts/`](docs/prompts/) — reusable prompts for stage work, reviews, and antifraud
6. [`docs/reports/`](docs/reports/) — completed stage reports

## Project in one sentence

Validate unique 8-digit customer promocodes at cashier points, close them safely, reconcile against Granit ERP sales, reduce cashier fraud, and give admin/viewer visibility with Telegram alerts.

## Current status (as of 2026-07-29)

- Project root: `D:\CursorProjects\promocode-checker`
- GitHub: https://github.com/IvanBondarenkoIT/promocode-checker
- Stages **1–9 done** (incl. 5.1, 6.1)
- Stage 9 CI/CD: **done** — `.github/workflows/ci.yml`, report `docs/reports/stage-09-cicd.md`
- Next: **Stage 10 — Runbooks polish**

## Hard process rules

- Work only in this directory: `promocode-checker` (not the old typo folder `promocode-chacker`).
- After every stage: tests → review → short report in `docs/reports/` → clarify open questions → **commit + push** → only then next stage.
- Stage prompts must always include this gate: see [`docs/prompts/stage-prompts.md`](docs/prompts/stage-prompts.md) and [`docs/prompts/project-prompts.md`](docs/prompts/project-prompts.md).
- Prefer local-first verification. Railway is demo. Windows Server Docker is production.
- **Do not ask whether to commit/push** — at stage end always commit on `feature/*`, merge to `develop`, push both (see [`docs/branching.md`](docs/branching.md)).
- Do not invent ERP schema assumptions beyond the documented coffee beans whitelist and proxy/direct modes.
- Do not re-ask locked decisions from `docs/decisions.md`.
- Product UI language is **English only** (cashier + admin).

## Environments

| Env | Purpose | Notes |
|-----|---------|-------|
| `local` | Development and tests | Postgres via `infra/docker-compose.yml` on port `5433` |
| `railway-demo` | Leadership demo | Railway + CI on branch `railway-demo` |
| `server-prod` | Real cashiers over RDP | Docker on Windows Server from `main` |

## Neighbor reference projects

- `D:\CursorProjects\granit-clients-based-segmentation` — coffee beans group IDs, segmentation logic
- `D:\CursorProjects\prices-monitoring-scrappers` — Railway + PROXY_API patterns
- `D:\CursorProjects\dimkava-big-book` — Docker prod compose patterns
- `D:\CursorProjects\stock-safety-monitor` — Railway cron/Telegram alert patterns
- `D:\CursorProjects\firebird-db-proxy` — ERP proxy access
