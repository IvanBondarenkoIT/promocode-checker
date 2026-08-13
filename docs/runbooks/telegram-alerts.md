# Telegram ops alerts (subscribe bot)

Ops notifications for promocode-checker. **Not** the customer barcode bot.

Bot: [@dimkava_promo_alerts_bot](https://t.me/dimkava_promo_alerts_bot)

## Subscribe (anyone)

1. Open the bot → `/start` (persistent buttons appear)
2. Send `promo` (or `TELEGRAM_SUBSCRIBE_KEYWORD`) → all topics on
3. Use buttons or presets to tune what you get
4. `/stop` to unsubscribe
5. `/demo` — sample message types **to you only**

### Persistent buttons

| Button | Action |
|--------|--------|
| Мои подписки | List of topics with ✅/⬜ and description |
| Настроить | Inline toggles per topic (tap to flip) |
| Проверить код | Prompt, then send 8–20 digits |
| Итоги дня | Preset: digests + system only |
| Помощь | Welcome / help text |

### Presets

| Command | Topics |
|---------|--------|
| `/full` | all six |
| `/digest` / «Итоги дня» | digest + system |
| `/critical` | fraud + system |
| `/sales` | sales + system |

Custom mix: **Настроить** (inline). Topic **system** is always on (🔒).

## Alert topics

| Topic | Events | Can disable? |
|-------|--------|--------------|
| `scans` | Cashier scans (any result) | yes |
| `closures` | Manual close + AUTO_CLOSE | yes |
| `sales` | ERP coffee sale observed (enough / not enough kg) | yes |
| `fraud` | Manual close without sale | yes |
| `digest` | Day start ~10:00, day end ~22:00 | yes |
| `system` | job_crash, digest_error, scope_switched | **no** |

Seed chats (`TELEGRAM_ALERT_CHAT_ID` / `TELEGRAM_CHAT_IDS`) always receive every topic.

Storage: `telegram_subscribers.topics` (CSV) + `alert_mode` label (`full` / `digest` / `critical` / `sales` / `custom`). Migration `009` backfills from the old `full`/`digest` modes.

## Check promocode status

Active subscribers only. Send `220000012523` or `/code 220000012523`.

Read-only: **no** `CheckerLog`, **no** broadcast alert.

Possible answers:

- активен / просрочен / не найден
- закрыт автоматически (продажа в ERP)
- закрыт вручную, продажа подтверждена
- закрыт вручную — ждём покупку в ERP (окно `FRAUD_MATCH_WINDOW_HOURS`)
- закрыт вручную без продажи — открыта тревога

## Poller

```powershell
python scripts/run_telegram_bot_poll.py --loop --timeout 25
```

On server-prod the **reconcile** container polls every ~5s (`scripts/run_reconcile_loop.py`).

## Daily digests (Asia/Tbilisi)

| When | Message |
|------|---------|
| **10:00** | «Рабочий день начался» + ERP coffee sales so far today |
| **22:00** | «Итог дня» — ERP coffee totals + checker counts |

## Env

```env
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_ALERT_CHAT_ID=<optional seed chat id>
TELEGRAM_CHAT_IDS=<optional comma-separated extra ids>
TELEGRAM_SUBSCRIBE_KEYWORD=promo
TELEGRAM_DEDUP_WINDOW_SECONDS=900
```

## Calibration pack

```powershell
python scripts/send_telegram_message_samples.py
```

## Server

Put token in `infra/.env.prod`, rebuild (`desktop\update-prod.ps1`), migrate through `009`, then `/start` + `promo` again if needed.
