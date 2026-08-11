# Runbook — Server production (Windows Server / RDP)

Real cashier points over RDP. Source of truth branch: **`main`**. Do not force-push `main`.

**Deploy root:** `C:\Projects\promocode-checker`  
**UI language:** English only.

## Architecture

```text
Windows Server Docker
  ├── db (Postgres)
  ├── app (FastAPI + static cashier/admin)
  └── reconcile (hourly loop)
RDP cashiers → desktop/launch-cashier.ps1 → Edge/Chrome --app= → FRONTEND_BASE_URL/?point_id=<shop>
```

Compose: [`../../infra/docker-compose.prod.yml`](../../infra/docker-compose.prod.yml)  
Env template: [`../../infra/.env.prod.example`](../../infra/.env.prod.example)  
Deploy notes: [`../reports/stage-08-deploy.md`](../reports/stage-08-deploy.md)

## Deploy (first time)

In PowerShell on the server (admin if Docker requires it):

```powershell
cd C:\Projects
git clone https://github.com/IvanBondarenkoIT/promocode-checker.git promocode-checker
cd C:\Projects\promocode-checker
git checkout main
git pull origin main

cd C:\Projects\promocode-checker\infra
Copy-Item .env.prod.example .env.prod
notepad .env.prod
# Change CRITICAL: APP_SECRET_KEY, POSTGRES_PASSWORD, ADMIN_PASSWORD, VIEWER_PASSWORD,
# PROXY_API_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_ALERT_CHAT_ID
# Keep AUTO_SEED_PROMOCODES=0

docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

Wait for migrations (entrypoint). Smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
# expect: status=ok, database=ok, schema=ok
```

Browser on the server (default prod port **8020** — avoids clash with other apps on 8000):

- Cashier: `http://127.0.0.1:8020/` (use desktop launcher so Shop = Windows username)
- Admin: `http://127.0.0.1:8020/admin/login`

After Stages 11a–11c (status hints, campaigns), also seed demo codes once:

```powershell
cd C:\Projects\promocode-checker\infra
Invoke-RestMethod http://127.0.0.1:8020/health
docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python /app/scripts/seed_promocodes.py
```

Then refresh cashier launcher (`desktop\config.json`: `cashierBaseUrl` = `http://127.0.0.1:8020`, empty `pointId`, `fullscreen` = `false`).  
Expect: **Shop** = Windows username of the RDP session, instruction under status, scan `10000001` → **ACTIVE** + **Campaign: Local demo wave**.  
Admin → tables → `campaigns` / `promocodes` (campaign columns).

Real promo wave CSV: [campaign-import.md](campaign-import.md).

Barcode PNGs (from a machine with Python/repo or via API):

```powershell
# API example
Invoke-WebRequest http://127.0.0.1:8020/api/v1/cashier/barcode/10000001 -OutFile 10000001.png
```

## ERP and Telegram

| Setting | Production |
|---------|------------|
| `ERP_ACCESS_MODE` | Prefer **`proxy`** from Docker (LAN Proxy API). Use `direct` only with `FIREBIRD_DSN=host.docker.internal/3055:DK_GEORGIA` + `fdb` in image |
| `FIREBIRD_*` | Readonly user; **do not** use `127.0.0.1` inside the container (that is not the Windows host) |
| `PROXY_API_*` | Required when mode=`proxy` |
| Telegram | Required — see [telegram-alerts.md](telegram-alerts.md) |

Coffee groups/products list: [`../coffee-beans-whitelist.txt`](../coffee-beans-whitelist.txt).  
Probe: [erp-probe.md](erp-probe.md).

Reconcile: hourly `run_reconcile_loop.py`. Smoke:

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml exec reconcile python /app/scripts/run_reconcile.py
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail 30 reconcile
```

## Update (later)

One-shot script (preferred):

```powershell
cd C:\Projects\promocode-checker\desktop
.\update-prod.ps1
```

Manual:

```powershell
cd C:\Projects\promocode-checker
git checkout main
git pull origin main
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

## Desktop launcher (RDP cashiers)

See [`../../desktop/README.md`](../../desktop/README.md).

On each RDP session (or shared profile template):

```powershell
cd C:\Projects\promocode-checker\desktop
Copy-Item config.example.json config.json
notepad config.json
```

Example when Docker runs on the **same** Windows Server:

```json
{
  "cashierBaseUrl": "http://127.0.0.1:8020",
  "pointId": "",
  "fullscreen": false,
  "browser": "auto"
}
```

Leave `pointId` empty — launcher uses the Windows RDP username as **Shop** / `point_id` (one Windows account per shop). Override `pointId` only for local tests.

```powershell
cd C:\Projects\promocode-checker\desktop
.\launch-cashier.ps1
```

Pin a desktop shortcut to `C:\Projects\promocode-checker\desktop\launch-cashier.ps1`.  
Verify hardware scanner (keyboard wedge + Enter) in app mode before go-live.

**Do not** point `cashierBaseUrl` at `localhost` on a remote RDP client unless the stack runs on that same machine.

## Campaign rollout (pre-production go-live)

Order matters: the global scope stays `TEST` until the data is verified.

```powershell
# 1. Back up before any import
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml exec db `
  pg_dump -U postgres promocode_checker > C:\Projects\backups\promocode_checker_$(Get-Date -Format yyyyMMdd-HHmm).sql

# 2. Update code and schema (migration 006 widens promocode to 8–20 digits)
cd C:\Projects\promocode-checker\desktop
.\update-prod.ps1

# 3. Copy the segment in and dry-run (promocode = loyalty card)
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml cp `
  C:\Projects\segments\segment.csv app:/app/data/input/segment.csv
docker compose --env-file .env.prod -f docker-compose.prod.yml exec app `
  python /app/scripts/import_segment_promocodes.py --file /app/data/input/segment.csv `
  --campaign-code beans_1_2kg_preprod --campaign-name "Coffee beans 1-2kg" `
  --kind LIVE --dry-run
```

If the campaign already has random 8-digit codes from an older import, run
`python /app/scripts/remap_promocode_to_card.py --campaign-code beans_1_2kg_preprod`
inside the app container (dry-run first), then regenerate the mailout.

Then run the import without `--dry-run`, copy the issued CSV out of the container
for the mailout, and only after checking the admin tables switch **Working data** to
`LIVE` on the dashboard ([campaign-scope.md](campaign-scope.md)).

Rollback of untouched codes: `python /app/scripts/import_segment_promocodes.py --rollback-campaign <code>`.

## General smoke / regression (prod server)

Run this after local OK and each promote to `main`. Prefer `desktop\update-prod.ps1` first.

```powershell
cd C:\Projects\promocode-checker\desktop
.\update-prod.ps1
```

Checklist:

1. **Health** — `Invoke-RestMethod http://127.0.0.1:8020/health` → `status=ok`, `database=ok`, `schema=ok`
2. **Cashier launch** — `.\launch-cashier.ps1`; **Shop** = Windows RDP username (`pointId` empty in `config.json`)
3. **Scan flows** — ACTIVE code → success UI; USED / EXPIRED / NOT FOUND show clear status
4. **Manual close** — close one ACTIVE; confirm USED; if Telegram configured, alert arrives for subscribers
5. **Admin** — login at `/admin/login`; lists / campaigns load
6. **Reconcile** — one-shot then logs:
   ```powershell
   cd C:\Projects\promocode-checker\infra
   docker compose --env-file .env.prod -f docker-compose.prod.yml exec reconcile python /app/scripts/run_reconcile.py
   docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail 40 reconcile
   ```
7. **Telegram** — `/start` → keyword `promo` → `/demo` against the **prod** bot token; confirm subscribe + sample types
8. **Scope guard** — with **Working data = TEST**, scan a `LIVE` customer code: the cashier must show `OTHER CAMPAIGN` and leave the code `ACTIVE`

Record pass/fail per item before handing cashiers a new build.

## Employee instructions

Give cashiers [`employee-cashier.md`](employee-cashier.md). UI labels are English (`Shop`, `Ready`, `Apply discount`, …).

## Rollback / ops notes

- Prefer redeploy previous `main` commit + `docker compose ... up -d --build`.
- TLS / reverse proxy (Caddy) is not in this compose; expose `PUBLIC_HTTP_PORT` on the internal network or add a proxy later.
- CI on `main` is lint/tests only — deploy stays manual Docker on the server ([`../branching.md`](../branching.md)).

## Related

- Env matrix: [`../env-matrix.md`](../env-matrix.md)
- Branching: [`../branching.md`](../branching.md)
