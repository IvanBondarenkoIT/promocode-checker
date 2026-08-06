# Telegram ops alerts (subscribe bot)

Ops notifications for promocode-checker. **Not** the customer barcode bot.

Bot: [@dimkava_promo_alerts_bot](https://t.me/dimkava_promo_alerts_bot)

## Subscribe (anyone)

1. Open the bot → `/start`
2. Send `promo` (or `TELEGRAM_SUBSCRIBE_KEYWORD`) → mode **full** (events + digests)
3. Switch mode:
   - `/full` or `полный` — all live events + day digests
   - `/digest` / `/итоги` / `итоги` — **only** day digests (+ errors always)
4. `/stop` to unsubscribe
5. `/demo` — sample message types **to you only**

Errors / crashes always go to every active subscriber (both modes).

A poller must be running (local or reconcile worker):

```powershell
# Local (keep running while testing the bot)
python scripts/run_telegram_bot_poll.py --loop --timeout 25
```

On server-prod the **reconcile** container polls every ~5s and runs a daily-digest tick each loop (`scripts/run_reconcile_loop.py`).

## Daily digests (Asia/Tbilisi)

| When | Message |
|------|---------|
| **10:00** | «Рабочий день начался» + ERP coffee sales so far today |
| **22:00** | «Итог дня» — ERP coffee totals/top products + checker counts (scans / manual / AUTO_CLOSE / fraud) |

On ERP failure for a digest: error alert to all; stamp is **not** advanced (retries next loop).

Env knobs:

```env
TELEGRAM_DAY_START_HOUR=10
TELEGRAM_DAY_START_MINUTE=0
TELEGRAM_EOD_HOUR=22
TELEGRAM_EOD_MINUTE=0
TELEGRAM_DIGEST_SALES_ROW_LIMIT=5000
```

Manual tick:

```powershell
python scripts/run_telegram_daily.py
```

## Env

```env
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_ALERT_CHAT_ID=<optional seed chat id>
TELEGRAM_CHAT_IDS=<optional comma-separated extra ids>
TELEGRAM_SUBSCRIBE_KEYWORD=promo
TELEGRAM_DEDUP_WINDOW_SECONDS=900
```

Recipients = active DB subscribers ∪ seed chat ∪ `TELEGRAM_CHAT_IDS`.  
Seed chats always receive **events** (treated as full).

## Calibration pack

```powershell
python scripts/send_telegram_message_samples.py
```

## Live event catalogue (Russian)

| Event | Audience | When |
|-------|----------|------|
| Скан промокода | full | Cashier check |
| Промокод закрыт вручную | full | Cashier redeem |
| Продажа кофе → автозакрытие | full | Reconcile AUTO_CLOSE |
| Тревога: без продажи | full | Fraud after MANUAL_CLOSE |
| Рабочий день начался | full+digest | ~10:00 |
| Итог дня | full+digest | ~22:00 |
| job_crash / digest_error / startup | all | Failures |

## Server

Put token in `infra/.env.prod`, rebuild (`desktop\update-prod.ps1`), migrate (004), then `/start` + `promo` again if needed.
