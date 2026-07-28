# Stage 05.1 Concurrent Redeem Lock Report

## Planned scope

- Protect redeem/close against double-close race (PostgreSQL row lock)
- Reuse shared close path for cashier redeem and reconcile auto-close
- Backend tests for sequential and concurrent double redeem
- Stage report + docs updates
- Commit and push at stage end (locked owner policy)

## Implementation

- [`backend/app/services/promocode_close.py`](../../backend/app/services/promocode_close.py):
  - `lock_promocode_by_code` / `lock_promocode_by_id` with `SELECT ... FOR UPDATE`
  - `close_promocode` raises `PromocodeAlreadyClosedError` if already USED
- [`backend/app/services/cashier.py`](../../backend/app/services/cashier.py):
  - `redeem_promocode` locks row before close; second redeem returns `used` without new log
- [`backend/app/jobs/reconcile.py`](../../backend/app/jobs/reconcile.py):
  - auto-close refetches row with lock; skips if no longer ACTIVE

## Tests

- `python -m ruff check .` → passed
- `python -m pytest tests/backend -v` → **31 passed**
  - new: `tests/backend/test_redeem_lock.py` (sequential + concurrent threads)

## Review notes

- Race between cashier redeem and reconcile auto-close is now serialized on the promocode row.
- No frontend changes required for 5.1.

## Risks and follow-ups / open questions

1. Stage 6 Admin UI can start after supervisor PASS on 5.1.
2. Stage 4.1 live Granit SQL validation still separate.
3. Hardware scanner RDP check remains before Stage 7.
