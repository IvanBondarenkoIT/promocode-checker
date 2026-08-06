# Pre-production calibration with shop cards

Goal: prove that a real coffee purchase on our own loyalty card closes a promocode
automatically and that the Telegram alert carries the right product, price and shop.

## 1. Collect the card ERP ids

`customer_id` must be the ERP `ORGN.ID` of the card (the same value reconcile sees as
`S.ORGNID`), not the printed card number. Put them in `data/input/staff_cards.csv`:

```text
customer_id,label
13961,Shop card Vake
14328,Shop card Saburtalo
```

Format example: [`../examples/staff_cards.example.csv`](../examples/staff_cards.example.csv)

## 2. Issue calibration codes

```powershell
python scripts/import_segment_promocodes.py `
  --file data/input/staff_cards.csv `
  --campaign-code preprod_calibration `
  --campaign-name "Preprod calibration" `
  --kind LIVE `
  --code-prefix 6
```

Codes land in `artifacts/campaigns/preprod_calibration_issued_*.csv`. Print barcodes:

```powershell
python scripts/export_dummy_barcodes.py --campaign-code preprod_calibration
```

## 3. Run the scenario

Switch the global scope to **LIVE** ([campaign-scope.md](campaign-scope.md)), then:

| Step | Expected |
|------|----------|
| Scan the calibration code at the cashier | `ACTIVE` + campaign name; Telegram scan alert |
| Buy whitelisted coffee beans on that card in the POS | ERP sale recorded |
| `python scripts/run_reconcile.py` | code becomes `USED` via `AUTO_CLOSE` |
| Telegram | "Продажа кофе → промокод закрыт автоматически" with product, price and `Скан раньше: да` |

Second scenario — manual close without a purchase:

| Step | Expected |
|------|----------|
| Scan + press Apply discount, buy nothing | `MANUAL_CLOSE` alert |
| Wait past `FRAUD_MATCH_WINDOW_HOURS` (2h) and run reconcile | fraud alert "Тревога: ручное закрытие без продажи кофе" |

Scope guard check: switch back to **TEST** and scan a `5`-prefixed customer code —
the cashier must answer `OTHER CAMPAIGN` and the code must stay `ACTIVE`.

## 4. Clean up

Untouched calibration codes can be removed; scanned or redeemed ones are kept for the
audit trail:

```powershell
python scripts/import_segment_promocodes.py --rollback-campaign preprod_calibration
```
