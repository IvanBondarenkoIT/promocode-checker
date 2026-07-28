# Environment Matrix

| Variable | Local | Railway demo | Server prod | Notes |
|----------|-------|--------------|-------------|-------|
| `APP_ENV` | `local` | `railway` | `prod` | |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker` | Railway Postgres | Docker compose Postgres / host | Use `+psycopg` |
| `PROMOCODE_TTL_DAYS` | 30 | 30 | as business needs | |
| `FRAUD_MATCH_WINDOW_HOURS` | 2 | 2 | 1–2 | soft amnesty |
| `ERP_ACCESS_MODE` | `proxy` or `mock` | `proxy` | `proxy` with `direct` fallback | |
| `PROXY_API_URL` | from sibling projects | required | required | |
| `PROXY_API_TOKEN` | secret | secret | secret | |
| `COFFEE_BEANS_GROUP_IDS` | `11077,16276,16279` | same | same | also in `config/coffee_beans_groups.json` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | local defaults | secrets | secrets | |
| `VIEWER_USERNAME` / `VIEWER_PASSWORD` | local defaults | secrets | secrets | |
| `TELEGRAM_BOT_TOKEN` | optional local | recommended | required | |
| `TELEGRAM_ALERT_CHAT_ID` | optional local | recommended | required | |
| `DEFAULT_POINT_ID` | `shop_01` | demo point | real shop ids | |

See `.env.example` for the full template.
