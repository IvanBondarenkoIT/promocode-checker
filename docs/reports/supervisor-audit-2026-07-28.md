# Supervisor Audit — 2026-07-28

External review of process vs plan for `promocode-checker`.

## Verdict summary

| Stage | Verdict | Notes |
|-------|---------|-------|
| 1 Bootstrap | **PASS** | Structure, venv, health, docs |
| 2 Data layer | **PASS** | Models, migration, generator, Postgres 5433 |
| 3 Cashier API | **PASS** | check/redeem/barcode + seed + tests |
| 4 ERP reconcile + Telegram | **PASS with conditions** | Core done on mock path; live ERP SQL not validated |

Overall process vs plan: **aligned**. Stage-gate reports exist for 01–04. Next planned stage: **5 Cashier PWA**.

## Stage 1 — PASS

- Correct folder `promocode-checker`
- FastAPI `/health`, `.env.example`, docs, AGENTS handoff later added
- Report complete

## Stage 2 — PASS

- All planned tables present
- Alembic `001_initial_schema`
- 8-digit constraint + TTL from env
- Compose Postgres on 5433
- Report complete

## Stage 3 — PASS

- Routes match plan/report:
  - `POST /api/v1/cashier/check`
  - `POST /api/v1/cashier/redeem`
  - `GET /api/v1/cashier/barcode/{code}`
- No cashier auth — matches decisions
- Seed script present
- Open risk correctly documented: concurrent redeem race

## Stage 4 — PASS with conditions

Matches plan checklist:

- ERP adapter mock/proxy/direct
- Reconcile CLI job
- AUTO_CLOSE + erp_sale_matched
- Fraud warnings + soft window 2h
- Coffee whitelist 11077/16276/16279
- Telegram + dedup
- Shared close helper
- Stage report claims **28 passed**

Conditions / not fully closed for production:

1. Live Granit SQL still draft — needs validation against real ERP/proxy
2. Discount marker not used — any whitelist coffee sale counts (explicitly noted)
3. Cron is external CLI only (in-app scheduler deferred to Stage 8 — acceptable)
4. Concurrent redeem race still open from Stage 3

## Process compliance

| Gate item | Status |
|-----------|--------|
| Tests per stage | Present in reports |
| Review notes | Present |
| Risks / open questions | Present (esp. Stage 4) |
| Locked decisions respected | Yes |
| Docs consistency | **Partial** — README was stale earlier; AGENTS/handoff/plan say Stages 1–4 done, next Stage 5 |

## Deviations (non-blocking)

1. Original plan path names `/api/v1/check` became `/api/v1/cashier/check` — acceptable namespacing, documented.
2. Coffee groups exist both as env and `config/coffee_beans_groups.json` — good; ensure runtime actually reads JSON or document env-as-source-of-truth.
3. Workspace still may be opened from typo folder in some Cursor sessions — operational risk.

## Before Stage 5 — gate CLOSED

See [`supervisor-gate-stage5-2026-07-28.md`](supervisor-gate-stage5-2026-07-28.md).

Locked answers:

1. Stage 4 accepted as done for local/mock; live ERP SQL = Stage 4.1 follow-up
2. Concurrent redeem lock deferred until **after** Stage 5
3. Telegram auto-close = **one summary per reconcile run**
4. Whitelist coffee sale match without discount column is enough for now

**Stage 5 Cashier PWA: APPROVED.**
