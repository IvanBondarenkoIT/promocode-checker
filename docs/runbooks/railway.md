# Runbook — Railway demo

Leadership / intermediate demo. Production cashiers use [server-prod.md](server-prod.md), not Railway.

**UI language:** English only.

## Branch and deploy path

| Item | Value |
|------|--------|
| Git branch | `railway-demo` |
| Deploy | Railway native GitHub connection (CI does **not** deploy) |
| Config | [`../../railway.toml`](../../railway.toml), [`../../infra/railway.toml`](../../infra/railway.toml) |
| Env template | [`../../infra/railway.env.example`](../../infra/railway.env.example) |
| CI | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) on push/PR to `railway-demo` |

Promote from `develop` when demo needs an update (see [`../branching.md`](../branching.md)).

## First-time setup

1. Create a Railway project; connect the GitHub repo; set branch to `railway-demo`.
2. Add a **Postgres** plugin (Railway injects `DATABASE_URL`; app normalizes `postgres://` → `postgresql+psycopg://`).
3. Set variables from [`infra/railway.env.example`](../../infra/railway.env.example):
   - `APP_ENV=railway`
   - `APP_SECRET_KEY` (strong secret)
   - `STATIC_DIR=/app/static` (Dockerfile default)
   - `FRONTEND_BASE_URL` / `RAILWAY_PUBLIC_DOMAIN` to the public host
   - `ADMIN_*` / `VIEWER_*`
   - `ERP_ACCESS_MODE=mock` for demo without live ERP (or `proxy` + token if demoing reconcile)
   - Optional: `AUTO_SEED_PROMOCODES=1`, Telegram vars
4. Deploy from Dockerfile (`railway.toml` healthcheck `/health`).
5. Confirm CI is green on `railway-demo` after the push.

## Smoke checklist

- `GET https://<domain>/health` → `"status":"ok"`, `"database":"ok"`, `"schema":"ok"`
- Cashier: `https://<domain>/?point_id=demo_01`
- Admin: `https://<domain>/admin/login`
- Scan a seeded code if auto-seed is enabled

## Notes

- Reconcile worker is part of **server-prod** compose, not the default single Railway web service. For demo, mock ERP + optional one-off `run_reconcile` is enough unless you add a second Railway service.
- Telegram: recommended for demo alerts; not required for UI smoke.
- Do not put real prod secrets only in Railway if the same values are needed on Windows Server — keep env files separate.

## Related

- Stage 8 deploy: [`../reports/stage-08-deploy.md`](../reports/stage-08-deploy.md)
- Env matrix: [`../env-matrix.md`](../env-matrix.md)
