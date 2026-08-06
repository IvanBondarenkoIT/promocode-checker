# Campaign scope: TEST vs LIVE

One global switch decides which campaigns the whole system serves. It exists so a
rehearsal can never close a real customer's promocode, and real codes cannot be
burned while the team is still testing.

| Where | Behaviour |
|-------|-----------|
| Campaign | `kind` = `TEST` or `LIVE`, fixed at creation (import refuses to flip it) |
| Switch | `app_settings.active_campaign_kind`, changed by an **admin** in the UI |
| Cashier | Codes outside the active kind return `OTHER CAMPAIGN` and are never redeemed |
| Reconcile | Auto-close and fraud checks only look at the active kind; `CLOSED` campaigns are skipped |
| Legacy codes | Promocodes with no campaign count as `TEST` and are never served in `LIVE` |
| Admin dashboard | Promocode counters follow the active kind |

Code prefixes keep ranges apart, so a code can only ever belong to one wave:

| Prefix | Use |
|--------|-----|
| `1`–`3` | Old `DEMO_LOCAL` seed |
| `4` | `auto_close_demo` (ERP probe) |
| `5` | Pre-production customer segment |
| `6` | Shop-card calibration |
| `9` | New test campaigns |

## Switching

Admin UI: **Dashboard → Working data → TEST / LIVE**. A reason is required; the
change lands in `admin_audit_logs` and fires a Telegram alert to every subscriber.

Check the current value any time:

```powershell
curl.exe -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/v1/admin/scope
```

## Go-live order

1. Import the segment with `--kind LIVE` while the switch is still `TEST`
2. Verify in the admin tables (filter by campaign / kind)
3. Calibrate auto-close on shop cards — [preprod-calibration.md](preprod-calibration.md)
4. Flip the switch to `LIVE` right before cashiers start
5. Scan one real code to confirm it is served

To pause a wave, switch back to `TEST`: nothing is deleted, real codes simply stop
being accepted.
