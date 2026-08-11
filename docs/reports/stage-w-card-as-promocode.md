# Stage W — Promocode = loyalty card (8–20 digits)

Date: 2026-08-11  
Branch: `feature/card-as-promocode`

## Goal

Cashiers scan the customer loyalty card. `promocode` stays a separate column but
segment import (and remap of older data) sets it equal to `customer_card`.

## Changes

| Area | What |
|------|------|
| Migration `006_promocode_length` | `promocodes.promocode` and `fraud_warnings.promocode_value` → `VARCHAR(20)`; check `^[0-9]{8,20}$` |
| Validation | `PROMOCODE_MIN_LENGTH=8`, `PROMOCODE_MAX_LENGTH=20` in generator; cashier API + barcode messages |
| Segment import | `promocode = card`; missing/invalid/colliding card → row error |
| Remap | `scripts/remap_promocode_to_card.py` + `promocode_remap` service for existing random codes |
| Cashier UI | `maxLength=20`; auto-submit only at **13** digits; Enter accepts any complete 8–20 |
| Docs | `decisions.md`, campaign-import / calibration / scope runbooks, AGENTS |

## Tests

- Backend: generator unit, barcode, campaign scope (card-as-code, require card, remap)
- Frontend: logic + CashierApp (13-digit auto-submit; no auto-submit on 8)

## Existing data

```powershell
python scripts/run_migrations.py
python scripts/remap_promocode_to_card.py --campaign-code beans_1_2kg_preprod --dry-run
python scripts/remap_promocode_to_card.py --campaign-code beans_1_2kg_preprod
```

Fallback: rollback untouched + re-import. Regenerate mailing Excel/PDF after remap.

## Open

- Promote to `main` + server: backup → migrate 006 → remap or import → mailout from server export
- Shop-card ERP ids still needed for calibration file
