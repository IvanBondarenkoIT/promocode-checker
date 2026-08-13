# Stage AD — Telegram topics + code lookup

Date: 2026-08-13

## Scope

- Split ops alerts into six topics with per-subscriber opt-in
- Persistent keyboard + inline topic toggles
- Read-only promocode status check from the bot chat

## Implementation

### Topics

| Topic | Events |
|-------|--------|
| scans | `cashier_scan` |
| closures | `cashier_manual_close`, `reconcile_auto_close` |
| sales | `sale_observed` |
| fraud | `fraud_warning` |
| digest | `day_start`, `day_end` |
| system | `job_crash`, `digest_error`, `scope_switched` (always on) |

- Migration `009_telegram_topics`: column `topics`, backfill from `alert_mode`
- Single map: `backend/app/services/telegram_topics.py`
- `send_alert(..., topic=)` replaces `audience=`
- Seed chats still get everything

### Bot UX

Persistent buttons: Мои подписки · Настроить · Проверить код · Итоги дня · Помощь  
Inline toggles under Настроить; `system` shown as 🔒.

### Code lookup

`backend/app/services/promocode_status.py` — eight states, no `CheckerLog` / no fan-out.  
Subscribers only. Digits or `/code <digits>`.

### Fraud confirm

`_fraud_check_manual_closes` sets `checker_logs.erp_sale_matched=True` when a sale is found in the window (enables `CLOSED_MANUAL_CONFIRMED` and skips re-query).

## Tests

- `test_telegram_topics.py` — routing, presets, toggles, callback
- `test_promocode_status.py` — all states + read-only
- `test_telegram_bot.py` — keyboard, subscriber vs stranger lookup
- `test_reconcile_job.py` — erp_sale_matched on confirmed manual close

## After deploy

1. `update-prod.ps1` (migration 009 runs via entrypoint)
2. In bot: `/start` → buttons → Настроить → flip a topic
3. Send a loyalty card number → status card

## Open questions

- None for this stage.
