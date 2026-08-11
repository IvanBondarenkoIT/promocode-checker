# Campaign import

Two import paths:

| Path | Codes | Use |
|------|-------|-----|
| **Segment import** (`import_segment_promocodes.py`) | **`promocode = loyalty card`** (8–20 digits; typically 13) | Real customer segments from the ERP/segmentation export |
| Wave import (`import_campaign_promocodes.py`) | taken from CSV | Marketing already has fixed codes |

Campaign `kind` (`TEST` / `LIVE`) plus the global scope switch decide which promocodes the cashier and reconcile actually serve — see [campaign-scope.md](campaign-scope.md).

**PII:** segment files and issued-code exports hold names, phones and card numbers. Keep them in `data/input/` and `artifacts/campaigns/` (both gitignored). Never commit them.

## Segment import (preferred)

CSV header (extra columns are ignored):

```text
customer_id,customer_name,customer_full_name,phone,...
```

- `customer_id` — ERP `ORGN.ID`; this is what reconcile matches against `S.ORGNID`
- `customer_name` — loyalty card number → stored as `customer_card` **and** as `promocode` (fields stay separate for a future split)
- `phone`, `customer_full_name` — optional

Example: [`../examples/segment.example.csv`](../examples/segment.example.csv)

Always dry-run first:

```powershell
python scripts/run_migrations.py
python scripts/import_segment_promocodes.py `
  --file data/input/coffee_beans_1_2_kg_12m.csv `
  --campaign-code beans_1_2kg_preprod `
  --campaign-name "Coffee beans 1-2kg preprod" `
  --kind LIVE `
  --ends-at 2026-09-30T23:59:59+04:00 `
  --dry-run
```

Drop `--dry-run` to write. The script then:

- sets `promocode` to the loyalty card (validated 8–20 digits, globally unique)
- skips customers already holding a code in this campaign (safe to re-run)
- writes `artifacts/campaigns/<campaign_code>_issued.csv` for the mailout
- sends a Telegram ops alert with campaign, kind and counts

Barcodes for the wave:

```powershell
python scripts/export_dummy_barcodes.py --campaign-code beans_1_2kg_preprod
```

## Remap older random codes → card

If a campaign was imported when codes were random 8-digit values, bring them to the card model after migration `006`:

```powershell
python scripts/remap_promocode_to_card.py --campaign-code beans_1_2kg_preprod --dry-run
python scripts/remap_promocode_to_card.py --campaign-code beans_1_2kg_preprod
```

Fallback: `--rollback-campaign` then re-import. Regenerate mailing Excel/PDF after remap — old 8-digit exports are wrong.

## Wave import (pre-made codes)

CSV columns:

```text
customer_erp_id,promocode
```

Example: [`../examples/campaign_wave.example.csv`](../examples/campaign_wave.example.csv)

```powershell
python scripts/import_campaign_promocodes.py `
  --file docs/examples/campaign_wave.example.csv `
  --campaign-code beans_wave_2026_08 `
  --campaign-name "Coffee beans Aug 2026" `
  --kind LIVE `
  --starts-at 2026-08-01T00:00:00+00:00 `
  --ends-at 2026-08-31T23:59:59+00:00 `
  --close-campaign beans_wave_2026_07
```

## Rollback

Removes only promocodes of that campaign that were never scanned or redeemed:

```powershell
python scripts/import_segment_promocodes.py --rollback-campaign beans_1_2kg_preprod
```

## Server prod

Back up first, then import inside the container (`AUTO_SEED_PROMOCODES=0`):

```powershell
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml exec db `
  pg_dump -U postgres promocode_checker > C:\Projects\backups\promocode_checker_before_import.sql

docker compose --env-file .env.prod -f docker-compose.prod.yml cp `
  C:\Projects\segments\segment.csv app:/app/data/input/segment.csv

docker compose --env-file .env.prod -f docker-compose.prod.yml exec app `
  python /app/scripts/import_segment_promocodes.py --file /app/data/input/segment.csv `
  --campaign-code beans_1_2kg_preprod --campaign-name "Coffee beans 1-2kg" --kind LIVE --dry-run
```

If older random codes already exist: run `remap_promocode_to_card.py` inside the app container before mailout.

Switch the global scope to `LIVE` only after the import looks right — [campaign-scope.md](campaign-scope.md).
