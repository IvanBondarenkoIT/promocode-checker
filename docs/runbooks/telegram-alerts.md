# Telegram ops alerts (separate bot)

Ops notifications for promocode-checker (auto-close summary, fraud, crashes).  
**Not** the customer barcode-delivery bot (see decisions — out of scope here).

## Create the bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot`
2. Name e.g. `Promocode Checker Alerts`, username e.g. `promocode_checker_alerts_bot`
3. Copy the bot **token**

## Get chat id

**DM to yourself**

1. Message the bot `/start`
2. Open: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Read `"chat":{"id": <number>}`

**Group**

1. Add the bot to a group, post any message
2. `getUpdates` → group `id` is usually negative (e.g. `-100…`)

## Local `.env`

```env
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALERT_CHAT_ID=<chat_id>
TELEGRAM_NOTIFY_OK=0
TELEGRAM_DEDUP_WINDOW_SECONDS=900
```

Smoke (no reconcile needed):

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
python scripts/send_test_telegram_alert.py
```

Expect a message in the chat and exit code 0.

## Server prod (`infra/.env.prod`)

```env
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALERT_CHAT_ID=<chat_id>
TELEGRAM_NOTIFY_OK=0
```

Restart so **app** and **reconcile** pick up env:

```powershell
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python /app/scripts/send_test_telegram_alert.py
```

## What gets sent

| Event | When |
|-------|------|
| `reconcile_auto_close` | One **summary** per reconcile run if any AUTO_CLOSE |
| `fraud_warning` | Each new fraud warning (deduped) |
| `job_crash` | Reconcile/startup failure (deduped hourly) |

Empty successful runs (`auto_closed=0`) do **not** spam Telegram.
