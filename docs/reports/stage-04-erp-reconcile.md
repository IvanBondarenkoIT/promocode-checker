# Stage 04 ERP Reconcile + Telegram Report

## Planned scope

- ERP adapter interface with `mock` / `proxy` / `direct` (+ proxy→direct fallback)
- Hourly reconcile job (CLI) for ACTIVE auto-close and MANUAL_CLOSE fraud checks
- Soft fraud window `FRAUD_MATCH_WINDOW_HOURS` (default 2h)
- Coffee beans match via group whitelist `11077,16276,16279`
- Telegram alerts with DB dedup (`telegram_notification_logs`)
- Shared close helper for cashier redeem and reconcile AUTO_CLOSE
- Tests + this stage report

## Implementation

- Shared close: `backend/app/services/promocode_close.py` (`close_promocode`)
  - cashier `redeem` → `MANUAL_CLOSE`
  - reconcile → `AUTO_CLOSE` + `erp_sale_matched=True`, `point_id=reconcile`
- ERP:
  - `backend/app/integrations/erp/` — types, base, mock, proxy, direct, factory, queries
  - Match rule: coffee group whitelist in date window (no invented discount column)
- Reconcile: `backend/app/jobs/reconcile.py` + `scripts/run_reconcile.py`
  - ACTIVE + coffee sale since `created_at` → AUTO_CLOSE
  - MANUAL_CLOSE past soft window without sale in ±window → `fraud_warnings` OPEN
- Telegram: `backend/app/services/telegram.py`
  - statuses: `sent`, `failed`, `skipped_dedup`, `skipped_no_config`
  - events: `reconcile_auto_close`, `fraud_warning`, `job_crash`

## Tests

- `python -m ruff check .` → passed (after line-length fix)
- `python -m pytest tests/backend -v` → **28 passed**
  - Stage 1–3 suite still green
  - New: mock ERP filter, reconcile auto-close/fraud/amnesty, Telegram dedup/fail/no-config

## Review notes

- Stage 4 core deliverables are in place on mock ERP path for local verification.
- Proxy/direct clients are wired; live SQL draft in `queries.py` still needs ERP validation.
- Cron wiring remains external (`python scripts/run_reconcile.py`); in-app scheduler is Stage 8.

## Risks and follow-ups / open questions

1. Exact Granit SQL tables/joins for coffee sales (draft uses DOCHEAD/DOCLINE/GOODS/CLIENTS aliases) — validate against live ERP / firebird-db-proxy before prod.
2. Discount filter: intentionally not invented; currently any whitelist coffee sale counts as match. Confirm whether ERP has a reliable discount marker.
3. Concurrent redeem race from Stage 3 still open (no row lock).
4. Before Stage 5 (cashier PWA): confirm `point_id` query param + heartbeat UX expectations are unchanged.
5. Should auto-close Telegram alerts be rate-limited per run summary instead of per code when many close at once?
