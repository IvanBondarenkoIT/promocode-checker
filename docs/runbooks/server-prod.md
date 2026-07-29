# Runbook — Server production (Windows Server / RDP)

Real cashier points over RDP. Source of truth branch: **`main`**. Do not force-push `main`.

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

## Deploy / update

1. On the server, clone or pull `main` into the deploy directory.
2. Prepare env:

```powershell
cd infra
Copy-Item .env.prod.example .env.prod
# Edit secrets: POSTGRES_PASSWORD, APP_SECRET_KEY, ADMIN_*, VIEWER_*, PROXY_API_TOKEN, TELEGRAM_*
# Set FRONTEND_BASE_URL and PUBLIC_HTTP_PORT to the host cashiers will open
```

3. Start stack:

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

4. Smoke:

- `http://<host>:<PUBLIC_HTTP_PORT>/health` → `status` / `database` / `schema` = ok
- Admin login with prod `ADMIN_*`
- Cashier URL with a real shop `point_id`

Entrypoint runs Alembic migrations on app start. Keep `AUTO_SEED_PROMOCODES=0` in prod.

## ERP and Telegram

| Setting | Production |
|---------|------------|
| `ERP_ACCESS_MODE` | `proxy` (primary); direct Firebird fallback only if configured |
| `PROXY_API_URL` / `PROXY_API_TOKEN` | Required for live reconcile |
| Telegram | Required for fraud / crash / reconcile summary alerts |

Reconcile service: `scripts/run_reconcile_loop.py` (hourly). Startup migration failure can notify via `scripts/notify_startup_failure.py` when Telegram is configured.

## Desktop launcher (RDP cashiers)

See [`../../desktop/README.md`](../../desktop/README.md).

1. Copy `desktop/config.example.json` → `desktop/config.json` **on each shop machine** (or shared template with per-shop overrides).
2. Set:

```json
{
  "cashierBaseUrl": "http://<server-host>:<port>",
  "pointId": "<real_shop_id>",
  "fullscreen": true,
  "browser": "auto"
}
```

3. Pin a shortcut to `desktop/launch-cashier.ps1`.
4. Verify hardware scanner (keyboard wedge + Enter) in app mode before go-live.

**Do not** point `cashierBaseUrl` at `localhost` on the RDP client unless the stack runs on that same machine.

## Employee instructions

Give cashiers [`employee-cashier.md`](employee-cashier.md). UI labels are English (`Shop`, `Ready`, `Apply discount`, …).

## Rollback / ops notes

- Prefer redeploy previous `main` commit + `docker compose ... up -d --build`.
- TLS / reverse proxy (Caddy) is not in this compose; expose `PUBLIC_HTTP_PORT` on the internal network or add a proxy later.
- CI on `main` is lint/tests only — deploy stays manual Docker on the server ([`../branching.md`](../branching.md)).

## Related

- Env matrix: [`../env-matrix.md`](../env-matrix.md)
- Branching: [`../branching.md`](../branching.md)
