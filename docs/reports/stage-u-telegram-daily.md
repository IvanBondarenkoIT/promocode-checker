# Stage U — Telegram daily digests + alert modes

## Scope

- Alert modes: `full` (events + digests) vs `digest` (day digests only)
- Errors always to all active subscribers
- Day-start digest ~10:00 Asia/Tbilisi (work started + ERP coffee so far)
- EOD digest ~22:00 (ERP coffee + checker event counts)
- Worker tick via `run_reconcile_loop.py`

## Implementation

| Area | Paths |
|------|--------|
| Migration | `004_telegram_alert_modes` — `alert_mode`, `telegram_digest_state` |
| Fan-out | `send_alert(..., audience=events\|digest\|errors)` |
| Daily job | `backend/app/jobs/telegram_daily.py`, `scripts/run_telegram_daily.py` |
| Templates | `msg_day_start`, `msg_day_end`, `msg_digest_error` |
| Bot | `/full`, `/digest` / `итоги` |
| ERP | `find_coffee_sales(..., all_customers=True)` for day totals |

## Verification

```powershell
python -m pytest tests/backend/test_telegram_daily.py tests/backend/test_telegram_dedup.py -q
```

10 passed (2026-08-04).

## Follow-ups

- Server: migrate 004 + token in `.env.prod` + rebuild
- Owner picks `/full` or `/digest` after subscribe
