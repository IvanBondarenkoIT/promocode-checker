# Stage 11a — Cashier User badge, status instructions, dummy barcodes

Date: 2026-07-30

## Planned scope

- Shop **User** badge (login-free; launcher passes Windows/`config.username`)
- Plain-English **status instructions** under every scan result
- Expand dummy seed to **20 ACTIVE** codes (`10000001`–`10000020`)
- CLI PNG export for dummy Code128 barcodes

## Implementation

- `frontend/src/cashier/operatorName.ts` + CashierApp Shop/User badge
- `resultInstruction()` in `frontend/src/cashier/logic.ts` + status panel UI
- `desktop/launch-cashier.ps1` appends `&username=`
- `scripts/seed_promocodes.py` — 20 ACTIVE + USED/EXPIRED samples
- `scripts/export_dummy_barcodes.py` → `artifacts/dummy-barcodes/` (gitignored)
- Docs: `employee-cashier.md`, `local.md`, `desktop/README.md`

## Tests

- Frontend vitest: **18** passed (instructions, operator name, USED instruction)
- Seed list assert: 20 ACTIVE / 24 total
- Export smoke: 24 PNGs written locally

## Review notes

- UI remains English-only
- Prod still `AUTO_SEED_PROMOCODES=0`; seed on server via one-shot `docker compose exec … seed_promocodes.py`
- Campaigns (Stage 11b) not started

## Risks / follow-ups

- Server needs rebuild + seed after pull for UI + codes
- Stage B: campaigns table + CSV import
- Stage C: show campaign on cashier/admin

## Open questions

None for 11a.
