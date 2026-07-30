# Campaign wave import

CSV columns (header required):

```text
customer_erp_id,promocode
```

Example: [`../examples/campaign_wave.example.csv`](../examples/campaign_wave.example.csv)

```powershell
python scripts/run_migrations.py
python scripts/import_campaign_promocodes.py `
  --file docs/examples/campaign_wave.example.csv `
  --campaign-code beans_wave_2026_08 `
  --campaign-name "Coffee beans Aug 2026" `
  --starts-at 2026-08-01T00:00:00+00:00 `
  --ends-at 2026-08-31T23:59:59+00:00 `
  --close-campaign beans_wave_2026_07
```

On server prod (`AUTO_SEED_PROMOCODES=0`):

```powershell
cd C:\Projects\promocode-checker
git pull origin main
cd infra
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python /app/scripts/import_campaign_promocodes.py --file /app/docs/examples/campaign_wave.example.csv --campaign-code demo_wave --campaign-name "Demo wave"
```

Copy your real CSV into the container or mount it before import.
