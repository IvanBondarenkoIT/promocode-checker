# Telegram ops alerts (subscribe bot)

Ops notifications for promocode-checker. **Not** the customer barcode bot.

Bot: [@dimkava_promo_alerts_bot](https://t.me/dimkava_promo_alerts_bot)

## Subscribe (anyone)

1. Open the bot → `/start`
2. Send `promo` (or `TELEGRAM_SUBSCRIBE_KEYWORD`)
3. Reply: you are subscribed
4. `/stop` to unsubscribe
5. `/demo` — send all sample message types **to you only** (visual calibration)

A poller must be running (local or reconcile worker):

```powershell
# Local (keep running while testing the bot)
python scripts/run_telegram_bot_poll.py --loop --timeout 25
```

On server-prod the **reconcile** container polls every ~5s (see `scripts/run_reconcile_loop.py`).

## Env

```env
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_ALERT_CHAT_ID=<optional seed chat id>
TELEGRAM_CHAT_IDS=<optional comma-separated extra ids>
TELEGRAM_SUBSCRIBE_KEYWORD=promo
TELEGRAM_DEDUP_WINDOW_SECONDS=900
```

Recipients = active DB subscribers ∪ seed chat ∪ `TELEGRAM_CHAT_IDS`.

## Calibration pack (all types)

```powershell
python scripts/send_telegram_message_samples.py
```

Sends `[DEMO n/N · label]` messages to every recipient (scans, manual close, auto-close, fraud, …).

## Live event catalogue (Russian)

| Event | When |
|-------|------|
| Скан промокода | Cashier check (ACTIVE / USED / EXPIRED / NOT FOUND) |
| Промокод закрыт вручную | Cashier redeem → wait for ERP sale (~2h) |
| Продажа кофе → автозакрытие | Reconcile AUTO_CLOSE (product, price ₾, order, prior scan shop) |
| Тревога: без продажи | Fraud after MANUAL_CLOSE without coffee sale in window |
| job_crash | Reconcile/startup failure |

Shop label: `point_id` (Windows username) or `config/shop_names.json`.

## Server

Put token in `infra/.env.prod`, rebuild (`desktop\update-prod.ps1`), then `/start` + `promo` again if needed.
