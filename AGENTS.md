# AGENTS.md — Promocode Checker

This file is the primary handoff for any Cursor agent working in this repository.

## Read first

1. [`docs/context-handoff.md`](docs/context-handoff.md) — current status and how to continue
2. [`docs/plan/IMPLEMENTATION_PLAN.md`](docs/plan/IMPLEMENTATION_PLAN.md) — full implementation plan
3. [`docs/decisions.md`](docs/decisions.md) — locked product and technical decisions
4. [`docs/business-requirements.md`](docs/business-requirements.md) — original business flow
5. [`docs/prompts/`](docs/prompts/) — reusable prompts for stage work, reviews, and antifraud
6. [`docs/reports/`](docs/reports/) — completed stage reports
7. [`docs/runbooks/`](docs/runbooks/) — local / server-prod / employee guides

## Project in one sentence

Validate unique customer promocodes (loyalty card / 8–20 digits) at cashier points, close them safely, reconcile against Granit ERP sales, reduce cashier fraud, and give admin/viewer visibility with Telegram alerts.

## Current status (as of 2026-08-13)

- Project root: `D:\CursorProjects\promocode-checker`
- GitHub: https://github.com/IvanBondarenkoIT/promocode-checker
- Stages **1–10 done** (incl. 5.1, 6.1); Stages **11a–11d** done
- Stage 4.1 ERP probe: **done** — live CSV OK + AUTO_CLOSE demo (`docs/reports/stage-41-erp-probe.md`)
- Gap checklist 2026-08-04: **done** (`docs/reports/gap-checklist-2026-08-04.md`)
- Stage T Telegram ops: **done**; Railway **dropped** (`docs/reports/drop-railway-2026-08-04.md`)
- Stage U Telegram daily digests + modes: **done** (`docs/reports/stage-u-telegram-daily.md`)
- Stage V pre-production segment + TEST/LIVE scope: **done** (`docs/reports/stage-v-preprod-segment.md`)
- Stage X monitor/enforce + 2 kg: **done** (`docs/reports/stage-x-monitor-mode.md`)
- Stage Z direct Firebird ERP on server: **done** — server probe PASS (`docs/reports/stage-z-direct-firebird.md`)
- Stage AA admin customer card forms: **done** (`docs/reports/stage-aa-admin-card-forms.md`)
- Next: LIVE scope + monitor `sale_observations` / Telegram on real sales; then owner switch to `enforce`

## Hard process rules

- Work only in this directory: `promocode-checker` (not the old typo folder `promocode-chacker`).
- After every stage: tests → review → short report in `docs/reports/` → clarify open questions → **commit + push** → only then next stage.
- Stage prompts must always include this gate: see [`docs/prompts/stage-prompts.md`](docs/prompts/stage-prompts.md) and [`docs/prompts/project-prompts.md`](docs/prompts/project-prompts.md).
- Prefer local-first verification, then **general / acceptance runs on server-prod**. No Railway.
- **Do not ask whether to commit/push** — at stage end always commit on `feature/*`, merge to `develop`, push both (see [`docs/branching.md`](docs/branching.md)).
- Do not invent ERP schema assumptions beyond the documented coffee beans whitelist and proxy/direct modes.
- Do not re-ask locked decisions from `docs/decisions.md`.
- Product UI language is **English only** (cashier + admin).
- Customer segments and issued-code exports are PII: keep them in `data/input/` and `artifacts/` (gitignored), never commit them.
- Campaign scope (`TEST` / `LIVE`) is enforced only in `backend/app/services/campaign_scope.py` — do not add parallel filters.
- Running the backend test suite drops the dev database; re-run `scripts/run_migrations.py` afterwards.

## Environments

| Env | Purpose | Notes |
|-----|---------|-------|
| `local` | Development and tests | Postgres via `infra/docker-compose.yml` on port `5433` — [runbooks/local.md](docs/runbooks/local.md) |
| `server-prod` | Real cashiers over RDP + acceptance smoke | Docker on Windows Server from `main` — [runbooks/server-prod.md](docs/runbooks/server-prod.md) |

## Neighbor reference projects

- `D:\CursorProjects\granit-clients-based-segmentation` — coffee beans group IDs, segmentation logic
- `D:\CursorProjects\prices-monitoring-scrappers` — PROXY_API patterns
- `D:\CursorProjects\dimkava-big-book` — Docker prod compose patterns
- `D:\CursorProjects\stock-safety-monitor` — Telegram alert / cron patterns
- `D:\CursorProjects\firebird-db-proxy` — ERP proxy access
