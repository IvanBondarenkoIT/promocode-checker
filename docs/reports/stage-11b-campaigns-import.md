# Stage 11b — Campaigns schema and CSV import

Date: 2026-07-30

## Planned scope

- `campaigns` table + `promocodes.campaign_id`
- CSV import for a promo wave
- Optional `--close-campaign` for previous wave

## Implementation

- Models: `Campaign`, `CampaignStatus`, FK on `Promocode`
- Migration: `backend/alembic/versions/002_campaigns.py`
- Service: `backend/app/services/campaign_import.py`
- CLI: `scripts/import_campaign_promocodes.py`
- Example CSV: `docs/examples/campaign_wave.example.csv`
- Runbook: `docs/runbooks/campaign-import.md`

## Tests

- `tests/backend/test_campaign_import.py` (requires Postgres `:5433`)
- Local Docker engine was down during this slice — CI Postgres service is the gate

## Review notes

- Existing promocodes keep `campaign_id=NULL`
- Import skips duplicate codes; invalid rows logged

## Follow-ups

- Stage 11c: cashier/admin display (same release train)
