# Stage AB — Coffee kg = SOURCE (already kg)

Date: 2026-08-13

## Problem

Monitor Telegram showed one 250 g pack as **0.06 кг** instead of **0.25 кг**:

```text
0.25 (SOURCE already kg) × 0.25 (GOODS.NW) = 0.0625
```

Live Granit (`granit-clients-based-segmentation` `qty_unit=kg`) stores pack weight in `STORZDTGDS.SOURCE`. Extra multiply by `GOODS.NW` was wrong. 1 kg packs looked OK by accident (`1 × 1`).

## Fix

`line_kg = STORZDTGDS.SOURCE` (already kg). Do not multiply by `GOODS.NW` / name / group fallbacks. NW stays metadata only.

## Tests

- `line_kg(0.25, stored_nw=0.25) == 0.25`
- `line_kg(2.0, group_id=16279) == 2.0`
- Reconcile not-enough uses SOURCE `0.5` kg

## After deploy

Historical `sale_observations` keep old kg. New sales after `update-prod.ps1` use correct kg. Dedup by `(customer_erp_id, order_id)` prevents re-alerts for old orders.

## Open questions

- None. Confirm on server: one 250 g line ≈ 0.25 kg in probe / next Telegram.
