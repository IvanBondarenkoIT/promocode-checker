# Stage Y — Shop ORGN monitor calibration (2026-08-11)

## Scope

Wire four ERP-approved shop ORGN ids into LIVE campaign `preprod_calibration`
under `PROMO_ENFORCEMENT_MODE=monitor` so coffee sales are observed + Telegram
without AUTO_CLOSE.

## Delivered

| Item | Detail |
|------|--------|
| CSV | `data/input/staff_cards.csv` (gitignored) + [`docs/examples/staff_cards.example.csv`](../examples/staff_cards.example.csv) |
| ORGNs | `21470`, `12523`, `14661`, `17306` |
| Codes | Synthetic `2200000`+ORGN (12 digits); reconcile matches `customer_erp_id` |
| Script | [`desktop/import-staff-calibration.ps1`](../../desktop/import-staff-calibration.ps1) |
| Runbook | [`docs/runbooks/preprod-calibration.md`](../runbooks/preprod-calibration.md) — monitor-first |
| Bugfix | `AdminRole` SQLAlchemy enum uses values (`admin`/`viewer`) so scope switch audit works |

## Verification (this machine prod compose)

- Campaign `preprod_calibration` kind=LIVE, 4 ACTIVE codes
- `app_settings.active_campaign_kind=LIVE`
- Dashboard `enforcement_mode=monitor`
- `run_reconcile.py` → `reconcile ok` (Proxy token required)
- `sale_observations` empty until a post-import coffee sale on those ORGNs

## Follow-ups

1. On Windows Server (`C:\Projects\...`): pull main, `update-prod.ps1`, ensure `PROXY_API_TOKEN`, run `import-staff-calibration.ps1`, set LIVE in Admin if needed.
2. Remap synthetic codes to real loyalty barcodes when known.
3. Full segment import after monitor looks healthy.
4. Flip to `enforce` only after several days of correct alerts.
