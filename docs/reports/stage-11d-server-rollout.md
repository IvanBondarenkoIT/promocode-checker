# Stage 11d — Server rollout checklist (11a–11c)

Date: 2026-07-30

## Planned scope

Operator steps to apply Stages 11a–11c on Windows Server prod (`main`, port **8020**).

## Seed change

`scripts/seed_promocodes.py` now upserts campaign **`DEMO_LOCAL`** (`Local demo wave`) and attaches all dummy codes so cashier shows the Campaign line.

## Server commands

```powershell
cd C:\Projects\promocode-checker
git checkout main
git pull origin main
cd infra
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
Invoke-RestMethod http://127.0.0.1:8020/health
docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python /app/scripts/seed_promocodes.py
```

Cashier: `desktop\config.json` → `cashierBaseUrl` `http://127.0.0.1:8020`, relaunch shortcut.

## Verify

1. Health ok/ok/ok  
2. Shop + User badge  
3. Scan `10000001` → ACTIVE + instruction + Campaign: Local demo wave  
4. Admin `/admin` → `campaigns` table  

## Follow-ups

- Real campaign CSV via [campaign-import.md](../runbooks/campaign-import.md)  
- Stage 4.1 live Granit SQL / TLS / GHCR still deferred  
