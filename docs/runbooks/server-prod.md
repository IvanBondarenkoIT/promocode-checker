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

- Cashier: `http://127.0.0.1:8020/?point_id=shop_01`
- Admin: `http://127.0.0.1:8020/admin/login`

## Update (later)

```powershell
cd C:\Projects\promocode-checker
git checkout main
git pull origin main
cd C:\Projects\promocode-checker\infra
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

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
| `ERP_ACCESS_MODE` | `direct` (preferred on Windows Server with local Firebird) |
| `FIREBIRD_DSN` / user / password | `127.0.0.1/3055:DK_GEORGIA` + readonly credentials |
| `PROXY_API_*` | Optional fallback if direct is unavailable |
| Telegram | Required for fraud / crash / reconcile summary alerts |

Coffee sales probe (validate SQL before trusting auto-close): [erp-probe.md](erp-probe.md).

Reconcile service: `scripts/run_reconcile_loop.py` (hourly). Startup migration failure can notify via `scripts/notify_startup_failure.py` when Telegram is configured.

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

## Employee instructions

Give cashiers [`employee-cashier.md`](employee-cashier.md). UI labels are English (`Shop`, `Ready`, `Apply discount`, …).

## Rollback / ops notes

- Prefer redeploy previous `main` commit + `docker compose ... up -d --build`.
- TLS / reverse proxy (Caddy) is not in this compose; expose `PUBLIC_HTTP_PORT` on the internal network or add a proxy later.
- CI on `main` is lint/tests only — deploy stays manual Docker on the server ([`../branching.md`](../branching.md)).

## Related

- Env matrix: [`../env-matrix.md`](../env-matrix.md)
- Branching: [`../branching.md`](../branching.md)
