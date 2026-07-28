# Stage 08 Deploy Report

## Scope

Docker image with static frontend, local full-stack compose, production compose, Railway demo config, healthchecks, restart policies, reconcile worker, startup crash Telegram hook.

## Implementation

- [`Dockerfile`](../Dockerfile) — multi-stage: Vite build → FastAPI + `/app/static`
- [`backend/app/static_files.py`](../backend/app/static_files.py) — SPA + assets from `STATIC_DIR`
- [`infra/docker-entrypoint.sh`](../infra/docker-entrypoint.sh) — migrations, optional seed, uvicorn; Telegram on migration failure
- [`infra/docker-compose.app.yml`](../infra/docker-compose.app.yml) — local stack with db compose overlay
- [`infra/docker-compose.prod.yml`](../infra/docker-compose.prod.yml) — prod db + app + hourly reconcile worker
- [`infra/railway.toml`](../infra/railway.toml) + [`railway.toml`](../railway.toml) — Railway healthcheck / restart
- [`infra/railway.env.example`](../infra/railway.env.example), [`infra/.env.prod.example`](../infra/.env.prod.example)
- [`scripts/run_reconcile_loop.py`](../scripts/run_reconcile_loop.py), [`scripts/notify_startup_failure.py`](../scripts/notify_startup_failure.py)
- Railway `postgres://` URL normalization in config

## Commands

**Local full stack:**
```powershell
docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build
# http://localhost:8000/?point_id=shop_01
# http://localhost:8000/admin/login
```

**Production (server):**
```powershell
cd infra
Copy-Item .env.prod.example .env.prod
# edit secrets
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

**Railway:** connect repo, add Postgres plugin, copy vars from `infra/railway.env.example`, deploy from `Dockerfile`.

## Tests

- Backend + infra: **42 passed** (static mount, config URL normalize, deploy asset smoke)
- Docker build: run manually on host with Docker Desktop

## Risks / follow-ups

1. Full `docker compose up --build` smoke not automated in CI (Stage 9).
2. Prod TLS/reverse proxy (Caddy) not included — expose `PUBLIC_HTTP_PORT` or add proxy in follow-up.
3. RDP desktop launcher should point `cashierBaseUrl` to prod host after deploy.

## Open questions

- None blocking Stage 9 CI/CD.
