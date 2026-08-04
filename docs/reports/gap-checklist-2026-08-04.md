# Gap checklist close-out (2026-08-04)

## Scope

Close items from the gap audit: ops Telegram runbook, ERP/direct Docker notes + `fdb`, reconcile Telegram summary, customer-bot decision, prod hygiene.

## Done in repo

| ID | Item | Result |
|----|------|--------|
| B1 | Ops Telegram bot setup | [`docs/runbooks/telegram-alerts.md`](../runbooks/telegram-alerts.md) + [`scripts/send_test_telegram_alert.py`](../../scripts/send_test_telegram_alert.py). Owner fills `.env.prod` on server. |
| B2–B3 | ERP / `fdb` | Optional extra `erp-direct` (`fdb`); Dockerfile installs `libfbclient2` + `.[erp-direct]`. Prod example prefers **proxy** from containers; direct uses `host.docker.internal`. Server smoke commands in [`server-prod.md`](../runbooks/server-prod.md). |
| C2 | One TG summary per reconcile | [`backend/app/jobs/reconcile.py`](../../backend/app/jobs/reconcile.py) + tests |
| C1 | Customer barcode bot | Locked in [`decisions.md`](../decisions.md): **out of scope**; barcode HTTP API only |
| B4–B7 / C9–C10 | Hygiene | [`desktop/update-prod.ps1`](../../desktop/update-prod.ps1); [`docs/coffee-beans-whitelist.txt`](../coffee-beans-whitelist.txt); supervisor/handoff/INDEX refreshed |

## Owner actions on Windows Server (not automatable here)

1. Put `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALERT_CHAT_ID` in `infra/.env.prod`, restart, run `send_test_telegram_alert.py` in app container.
2. Confirm `ERP_ACCESS_MODE` (`proxy` recommended for Docker). Keep `PROXY_API_TOKEN` if proxy.
3. `.\desktop\update-prod.ps1` then check reconcile logs / health.
4. Ensure `desktop\config.json` has `"pointId": ""`.
5. Optional: seed demo + hardware scanner smoke; real campaign CSV when marketing ready.
6. Optional later: Railway `railway-demo` connection, TLS, GHCR.

## Verification (local)

```powershell
python -m pytest tests/backend/test_reconcile_job.py -q
python -m ruff check backend/app/jobs/reconcile.py scripts/send_test_telegram_alert.py
```

## Open / deferred (by design)

- Discount-column ERP filter
- Admin-editable coffee whitelist UI
- Auto CD to Windows Server
- TLS / GHCR / Railway confirm
