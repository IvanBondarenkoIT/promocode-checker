# Stage 11c — Campaign info in cashier and admin UI

Date: 2026-07-30

## Planned scope

- Cashier check/redeem response includes campaign fields
- Cashier status panel shows **Campaign: …** when present
- Admin tables: `campaigns` browse + promocodes enriched with `campaign_code` / `campaign_name`

## Implementation

- `CashierCodeResponse`: `campaign_code`, `campaign_name`, `campaign_ends_at`
- Cashier joinedload campaign on check; lazy load after redeem lock
- Admin `AdminTableName.CAMPAIGNS` + dashboard link
- Frontend status line + dashboard `campaigns` table

## Tests

- Frontend: campaign line render test
- Backend campaign import tests (11b) cover data path

## Review notes

- No campaign → no extra cashier line (dummy codes OK)
- English only

## Open questions

None.
