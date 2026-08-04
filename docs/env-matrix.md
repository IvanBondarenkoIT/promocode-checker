# Environment Matrix

Single reference for variables across **local**, **Railway demo**, and **server-prod**.  
How-to guides: [`runbooks/`](runbooks/README.md). Templates: [`.env.example`](../.env.example), [`infra/railway.env.example`](../infra/railway.env.example), [`infra/.env.prod.example`](../infra/.env.prod.example).

## Core

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `APP_ENV` | `local` | `railway` | `prod` | |
| `APP_HOST` | `0.0.0.0` | container default | container default | |
| `APP_PORT` / `PORT` | `8000` | Railway `PORT` | `8000` | entrypoint prefers `PORT` then `APP_PORT` |
| `APP_TIMEZONE` | `Asia/Tbilisi` | same | same | |
| `APP_SECRET_KEY` | local default | **secret** | **secret** | admin token signing |

## Database

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker` | Railway Postgres plugin | built from `POSTGRES_*` or explicit URL | normalize `postgres://` → `+psycopg` |
| `POSTGRES_HOST` | n/a (URL) | n/a | `db` | prod compose |
| `POSTGRES_PORT` | n/a | n/a | `5432` | |
| `POSTGRES_DB` | n/a | n/a | `promocode_checker` | |
| `POSTGRES_USER` | n/a | n/a | `postgres` | |
| `POSTGRES_PASSWORD` | n/a | n/a | **secret** | required in `.env.prod` |

## Promo / fraud

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `PROMOCODE_TTL_DAYS` | `30` | `30` | as business needs | |
| `FRAUD_MATCH_WINDOW_HOURS` | `2` | `2` | `1`–`2` | soft amnesty |

## ERP

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `ERP_ACCESS_MODE` | `proxy` (probe) or `mock` | usually `mock` | `direct` (primary) | probe: [runbooks/erp-probe.md](runbooks/erp-probe.md) |
| `PROXY_API_URL` | required for proxy | if proxy | optional fallback | e.g. `http://178.63.72.227:8010` |
| `PROXY_API_TOKEN` | **secret** if proxy | if proxy | optional **secret** | |
| `PROXY_API_TIMEOUT` | `60` | `60` | `60` | |
| `PROXY_API_MAX_RETRIES` | `3` | `3` | `3` | |
| `FIREBIRD_DSN` | empty | empty | `127.0.0.1/3055:DK_GEORGIA` | same host as firebird-db-proxy |
| `FIREBIRD_USER` | empty | empty | readonly user | |
| `FIREBIRD_PASSWORD` | empty | empty | **secret** | never commit |

## Coffee matching

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `COFFEE_BEANS_GROUP_IDS` | `11077,16276,16279` | same | same | also `config/coffee_beans_groups.json` |
| `COFFEE_BEANS_PARAM_ID` | `2` | same | same | |
| `COFFEE_BEANS_PARAM_VALUE_ID` | `4` | same | same | |
| `ERP_PAID_STATUSES` | `1,2,3,5` | same | same | STORZAKAZDT paid statuses |

## Cashier / desktop

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `DEFAULT_POINT_ID` | `shop_01` | demo point | real shop ids | URL `?point_id=` overrides |
| `CASHIER_SESSION_HEARTBEAT_SECONDS` | `60` | `60` | `60` | |
| `DESKTOP_DEFAULT_POINT_ID` | `shop_01` | n/a | per-machine `config.json` | desktop wrapper |

## Admin auth

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | defaults in `.env` | **secrets** | **secrets** | |
| `VIEWER_USERNAME` / `VIEWER_PASSWORD` | defaults | **secrets** | **secrets** | read-only |

## Telegram

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | optional | recommended | **required** | |
| `TELEGRAM_ALERT_CHAT_ID` | optional | recommended | **required** | |
| `TELEGRAM_NOTIFY_OK` | `0` | `0` | `0` | |
| `TELEGRAM_DEDUP_WINDOW_SECONDS` | `900` | `900` | `900` | |

## Frontend / HTTP

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `FRONTEND_BASE_URL` | `http://localhost:8000` or `:5173` CORS | `https://$RAILWAY_PUBLIC_DOMAIN` | server URL | CORS + same-origin static |
| `STATIC_DIR` | empty (Vite) or auto `frontend/dist` | `/app/static` | `/app/static` | Docker image |
| `RAILWAY_PUBLIC_DOMAIN` | empty | public host | empty | CORS https origin |
| `PUBLIC_HTTP_PORT` | `8000` | `8000` | host publish port | compose mapping |
| `AUTO_SEED_PROMOCODES` | `1` in app compose | `1` for demo | `0` | entrypoint seed |

## Docker / deploy pointers

- Local stack: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build` — [runbooks/local.md](runbooks/local.md)
- Prod: `infra/docker-compose.prod.yml` + `infra/.env.prod` — [runbooks/server-prod.md](runbooks/server-prod.md)
- Railway: `railway.toml` + `infra/railway.env.example` — [runbooks/railway.md](runbooks/railway.md)
