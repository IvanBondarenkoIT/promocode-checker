# Environment Matrix

Single reference for variables across **local** and **server-prod**.  
How-to guides: [`runbooks/`](runbooks/README.md). Templates: [`.env.example`](../.env.example), [`infra/.env.prod.example`](../infra/.env.prod.example).

## Core

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `APP_ENV` | `local` | `prod` | |
| `APP_HOST` | `0.0.0.0` | container default | |
| `APP_PORT` / `PORT` | `8000` | `8000` | entrypoint prefers `PORT` then `APP_PORT` |
| `APP_TIMEZONE` | `Asia/Tbilisi` | same | |
| `APP_SECRET_KEY` | local default | **secret** | admin token signing |

## Database

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker` | built from `POSTGRES_*` or explicit URL | normalize `postgres://` → `+psycopg` |
| `POSTGRES_HOST` | n/a (URL) | `db` | prod compose |
| `POSTGRES_PORT` | n/a | `5432` | |
| `POSTGRES_DB` | n/a | `promocode_checker` | |
| `POSTGRES_USER` | n/a | `postgres` | |
| `POSTGRES_PASSWORD` | n/a | **secret** | required in `.env.prod` |

## Promo / fraud

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `PROMOCODE_TTL_DAYS` | `30` | as business needs | |
| `FRAUD_MATCH_WINDOW_HOURS` | `2` | `1`–`2` | soft amnesty |
| `PROMO_ENFORCEMENT_MODE` | `monitor` | `monitor` → later `enforce` | observe+TG vs auto-close; [enforcement-modes.md](runbooks/enforcement-modes.md) |
| `PROMO_MIN_COFFEE_KG` | `2.0` | `2.0` | kg in one order (SOURCE × GOODS.NW) |
| `RECONCILE_INTERVAL_SECONDS` | `3600` | `900` while monitoring | min 60 |

## ERP

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `ERP_ACCESS_MODE` | `proxy` (probe) or `mock` | Prefer `proxy` from Docker; `direct` via `host.docker.internal` | probe: [runbooks/erp-probe.md](runbooks/erp-probe.md) |
| `PROXY_API_URL` | required for proxy | LAN Proxy API | e.g. `http://178.63.72.227:8010` |
| `PROXY_API_TOKEN` | **secret** if proxy | **secret** if proxy | |
| `PROXY_API_TIMEOUT` | `60` | `60` | |
| `PROXY_API_MAX_RETRIES` | `3` | `3` | |
| `FIREBIRD_DSN` | empty | `host.docker.internal/3055:DK_GEORGIA` if direct | not `127.0.0.1` inside container |
| `FIREBIRD_USER` | empty | readonly user | |
| `FIREBIRD_PASSWORD` | empty | **secret** | never commit |

## Coffee matching

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `COFFEE_BEANS_GROUP_IDS` | `11077,16276,16279` | same | also `config/coffee_beans_groups.json` |
| `COFFEE_BEANS_PARAM_ID` | `2` | same | |
| `COFFEE_BEANS_PARAM_VALUE_ID` | `4` | same | |
| `ERP_PAID_STATUSES` | `1,2,3,5` | same | STORZAKAZDT paid statuses |

## Cashier / desktop

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `DEFAULT_POINT_ID` | `shop_01` | real shop ids | URL `?point_id=` overrides |
| `CASHIER_SESSION_HEARTBEAT_SECONDS` | `60` | `60` | |
| `DESKTOP_DEFAULT_POINT_ID` | `shop_01` | per-machine `config.json` | desktop wrapper |

## Admin auth

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | defaults in `.env` | **secrets** | |
| `VIEWER_USERNAME` / `VIEWER_PASSWORD` | defaults | **secrets** | read-only |

## Telegram

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | optional | **required** | |
| `TELEGRAM_ALERT_CHAT_ID` | optional seed | optional seed | subscribers via bot `promo` |
| `TELEGRAM_NOTIFY_OK` | `0` | `0` | |
| `TELEGRAM_DEDUP_WINDOW_SECONDS` | `900` | `900` | |
| `TELEGRAM_DAY_START_HOUR` | `10` | `10` | Asia/Tbilisi digest |
| `TELEGRAM_EOD_HOUR` | `22` | `22` | Asia/Tbilisi digest |

## Frontend / HTTP

| Variable | Local | Server prod | Notes |
|----------|-------|-------------|-------|
| `FRONTEND_BASE_URL` | `http://localhost:8000` or `:5173` CORS | server URL (e.g. `http://127.0.0.1:8020`) | CORS + same-origin static |
| `STATIC_DIR` | empty (Vite) or auto `frontend/dist` | `/app/static` | Docker image |
| `PUBLIC_HTTP_PORT` | `8000` | host publish port | compose mapping |
| `AUTO_SEED_PROMOCODES` | `1` in app compose | `0` | entrypoint seed |

## Docker / deploy pointers

- Local stack: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.app.yml up --build` — [runbooks/local.md](runbooks/local.md)
- Prod: `infra/docker-compose.prod.yml` + `infra/.env.prod` — [runbooks/server-prod.md](runbooks/server-prod.md)
- General acceptance tests: smoke checklist in [runbooks/server-prod.md](runbooks/server-prod.md)
