# Stage T — Telegram ops subscribe + human alerts

## Scope

- Multi-subscriber bot (stock-safety pattern)
- Russian human-readable alerts for scan / manual close / AUTO_CLOSE / fraud
- `/demo` + CLI sample pack for visual calibration
- ERP sale `UNIT_PRICE` on AUTO_CLOSE; prior SCAN_CHECK shop

## Implementation

| Area | Paths |
|------|--------|
| Migration | `003_telegram_subscribers` |
| Models | `TelegramSubscriber`, `TelegramBotState` |
| Fan-out | `backend/app/services/telegram.py` |
| Templates | `telegram_messages.py` |
| Bot poll | `telegram_bot.py`, `scripts/run_telegram_bot_poll.py` |
| Samples | `scripts/send_telegram_message_samples.py`, bot `/demo` |
| Cashier hooks | `cashier.py` scan + manual close |
| Reconcile | per-code rich AUTO_CLOSE + fraud template |
| Worker | `run_reconcile_loop.py` polls bot every 5s |
| Runbook | `docs/runbooks/telegram-alerts.md` |

## How to use

1. `python scripts/run_telegram_bot_poll.py --loop --timeout 25`
2. Telegram: `/start` → `promo` → `/demo` (or CLI samples)
3. Live cashier/reconcile alerts go to all subscribers

Local Windows may need `TELEGRAM_DISABLE_SSL_VERIFY=1`.

## Verification

- ruff + pytest reconcile/telegram/erp queries
- Bot poll handled pending updates (`handled=6` on first live poll)

## Follow-ups

- Owner: say `promo` if not subscribed yet; review DEMO copy and request wording tweaks
- Server: token + SSL defaults in `.env.prod`, `update-prod.ps1`
