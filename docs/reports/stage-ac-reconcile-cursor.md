# Stage AC — Reconcile cursor + 10-minute polling

Date: 2026-08-13

## Scope

- Poll ERP every **10 minutes** (`RECONCILE_INTERVAL_SECONDS=600`).
- Stop growing the Firebird window from the oldest active promocode.
- Do not miss sales at window seams (`S.DAT_` is date-only / midnight).
- Count a sale on the **same calendar day** the code was issued (`APP_TIMEZONE`).

## Implementation

Persistent one-row table `reconcile_state` (migration `008_reconcile_state`):

- `last_scan_until` — cursor
- `last_run_at`, `last_erp_rows`, `last_erp_ms` — timing for ops

Window:

```text
raw_since = oldest_active.created_at                 # first run
raw_since = max(oldest_active.created_at,
                last_scan_until - RECONCILE_OVERLAP_HOURS)  # later
since     = start of local day(raw_since)            # DAT_ midnight
until     = now
```

After a successful observe pass, `last_scan_until = until` in the same transaction. ERP errors roll back; the cursor does not move. Overlap default **48 hours**. Duplicates are skipped by `uq_sale_observations_customer_order` (one bulk lookup per run).

Connection model unchanged: connect → one SELECT → close. No pool.

## Tests

- `tests/backend/test_reconcile_cursor.py` — first/steady/downtime windows, ERP error leaves cursor, same-day sale counted, previous day skipped, no duplicate observation/alert
- Existing `tests/backend/test_reconcile_job.py` still covers auto-close / monitor / fraud

## After deploy (server)

In `infra/.env.prod` set (then `desktop\update-prod.ps1`):

```text
RECONCILE_INTERVAL_SECONDS=600
RECONCILE_OVERLAP_HOURS=48
```

Check worker logs:

```text
reconcile worker started; reconcile_interval=600s ...
reconcile window since=... until=... rows=N erp_ms=M observed=K
```

Steady `since` should sit about 48 h (plus local-midnight floor) behind `until`, not the campaign start date.

## Risks / follow-ups

- Historical `sale_observations` are unchanged; already-alerted orders stay deduped.
- Fraud check still uses its own ±2 h window around `MANUAL_CLOSE` (not this cursor).
- `CAST(S.ORGNID …)` still prevents a native Firebird index on customer; 48 h of coffee lines for ~180 cards should stay small. Revisit if `erp_ms` grows.

## Open questions

- None for this stage. Confirm on server: interval 600s and `since` does not walk back to import day.
