# Pre-production calibration with shop cards

Goal: prove ERP coffee sales on practice shop ORGNs are observed (monitor) and later
auto-close in enforce, with correct Telegram product / kg / shop context.

## 1. Approved shop ORGN ids (monitor first)

These four ORGN ids were confirmed via ERP probe (coffee sales on shop cards).
Loyalty barcodes are not in repo yet — use **synthetic** 12-digit codes
(`2200000` + ORGN) so import validates. Reconcile matches by `customer_erp_id`,
so purchase monitoring works without real card scans.

Put them in `data/input/staff_cards.csv` (gitignored; copy of the committed example):

```text
customer_id,customer_name,customer_full_name
21470,220000021470,Shop DK BATUMI
12523,220000012523,Shop PALIASHVILI
14661,220000014661,Shop BATUMI MALL
17306,220000017306,Shop EAST POINT
```

Format example: [`../examples/staff_cards.example.csv`](../examples/staff_cards.example.csv)  
Catalog: [`../../config/test_shop_cards.json`](../../config/test_shop_cards.json)

When real loyalty numbers are known, remap with `scripts/remap_promocode_to_card.py`
(or re-import) so cashiers can scan physical cards.

## 2. Issue calibration codes

Local:

```powershell
python scripts/import_segment_promocodes.py `
  --file data/input/staff_cards.csv `
  --campaign-code preprod_calibration `
  --campaign-name "Preprod calibration" `
  --kind LIVE `
  --dry-run
# drop --dry-run to write
```

Server-prod (preferred one-shot): [`../../desktop/import-staff-calibration.ps1`](../../desktop/import-staff-calibration.ps1)

```powershell
cd C:\Projects\promocode-checker\desktop
.\import-staff-calibration.ps1
```

Codes land in `artifacts/campaigns/preprod_calibration_issued_*.csv`.
Optional barcodes (synthetic codes only):

```powershell
python scripts/export_dummy_barcodes.py --campaign-code preprod_calibration
```

## 3. Scope and enforcement

1. Keep `PROMO_ENFORCEMENT_MODE=monitor` in `infra/.env.prod`.
2. Admin → Working data → **LIVE** (reason required).
3. Dashboard badge: Enforcement **Monitor**.

Without LIVE scope, reconcile ignores this LIVE campaign.

## 4. Monitor scenario (current go-live)

| Step | Expected |
|------|----------|
| Shop POS sells whitelisted coffee on one of the four ORGNs | ERP sale |
| `python scripts/run_reconcile.py` (or wait up to `RECONCILE_INTERVAL_SECONDS`) | `sale_observations` row; Telegram sale-observed |
| Promocode | stays **ACTIVE** (no AUTO_CLOSE in monitor) |

Sales with `sold_at` **before** promocode `created_at` are ignored — no backdate unless
you intentionally replay the same day.

Cashier scan of the synthetic code is optional; physical shop barcodes will not match
until remapped to real card numbers.

## 5. Enforce scenario (later)

Set `PROMO_ENFORCEMENT_MODE=enforce`, recreate containers, buy ≥ `PROMO_MIN_COFFEE_KG`
(2.0) in one order → expect `USED` + AUTO_CLOSE Telegram.

Second scenario — manual close without a purchase:

| Step | Expected |
|------|----------|
| Scan + Apply discount, buy nothing | `MANUAL_CLOSE` alert |
| Wait past `FRAUD_MATCH_WINDOW_HOURS` (2h) and run reconcile | fraud alert |

Scope guard: switch back to **TEST** and scan a LIVE code —
cashier must answer `OTHER CAMPAIGN`; code stays `ACTIVE`.

## 6. Clean up

Untouched calibration codes can be removed; scanned or redeemed ones are kept:

```powershell
python scripts/import_segment_promocodes.py --rollback-campaign preprod_calibration
```
