# Stage Z — Direct Firebird ERP on server (2026-08-12)

## Scope

Stop reconcile / daily digest failures caused by unreachable Proxy API from server Docker.
Use direct Firebird on the same Windows host; keep monitor mode and Telegram alerts unchanged.

## Delivered

| Area | Paths |
|------|-------|
| Config | `FIREBIRD_LIBRARY_PATH` in [config.py](../../backend/app/core/config.py) |
| Direct adapter | [direct.py](../../backend/app/integrations/erp/direct.py) — `fb_library_name`, DSN in errors, `server_version()` |
| Factory | [factory.py](../../backend/app/integrations/erp/factory.py) — direct primary + optional proxy fallback |
| Probe | [scripts/probe_erp_direct.py](../../scripts/probe_erp_direct.py), [desktop/check-erp.ps1](../../desktop/check-erp.ps1) |
| Compose | [infra/docker-compose.prod.yml](../../infra/docker-compose.prod.yml) — `extra_hosts`, default `ERP_ACCESS_MODE=direct` |
| Env | [infra/.env.prod.example](../../infra/.env.prod.example) |
| CI | Ruff E501 fix; `tests/infra` in workflow |
| Tests | [tests/backend/test_erp_direct_adapter.py](../../tests/backend/test_erp_direct_adapter.py) |

## Local verification

Against `D:\CursorProjects\DB-copy\GEORGIA.GDB` via FB 2.5 embedded:

- `Engine version: 2.5.9` — connect OK
- Coffee sales empty for shop ORGNs in 30-day window (expected on stale July copy)
- `pytest tests/backend tests/infra` — 45 passed (integration tests skip without Postgres)

## Server rollout (owner)

1. Pull `main`, edit `infra/.env.prod`:

```env
ERP_ACCESS_MODE=direct
FIREBIRD_DSN=host.docker.internal/3050:C:/db/GEORGIA.GDB
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=<same as firebird-db-proxy DB_PASSWORD>
FIREBIRD_LIBRARY_PATH=
PROMO_ENFORCEMENT_MODE=monitor
```

2. `cd desktop; .\update-prod.ps1`
3. `.\check-erp.ps1 -CustomerIds "21470,12523,14661,17306" -Days 7`
4. Confirm reconcile logs: `reconcile ok` (no `Connection refused`)
5. Keep scope **LIVE** + monitor; watch `sale_observations` / Telegram on next coffee sale

## Server verification (2026-08-13)

On `C:\Projects\promocode-checker` after aligning `.env.prod` with the working Firebird proxy:

```env
ERP_ACCESS_MODE=direct
FIREBIRD_DSN=host.docker.internal/3050:C:/db/GEORGIA.GDB
FIREBIRD_USER=SYSDBA
FIREBIRD_LIBRARY_PATH=
PROMO_ENFORCEMENT_MODE=monitor
```

| Check | Result |
|-------|--------|
| `check-erp.ps1 -CustomerIds "21470,12523,14661,17306" -Days 7` | `Engine version: 2.5.9` |
| Sales window | **91** lines / **78** unique orders |
| Reconcile logs | `reconcile ok auto_closed=0 fraud_warnings=0` (monitor) |

### Pitfalls fixed during rollout

| Wrong | Correct |
|-------|---------|
| `FIREBIRD_LIBRARY_PATH=C:\db\GEORGIA.GDB` | Leave empty in Linux Docker; GDB path belongs in `FIREBIRD_DSN` only |
| `host.docker.internal/3055:DK_GEORGIA` | Match proxy: port **3050** + `C:/db/GEORGIA.GDB` |
| Remote Proxy API as primary | Direct to host Firebird; local proxy optional fallback |

Guard: if `FIREBIRD_LIBRARY_PATH` ends with `.gdb`/`.fdb`, the direct adapter ignores it (misconfig safety).

## Risks

- Firebird IP whitelist may block Docker bridge (172.x) — probe error will show DSN; allow bridge or use host firewall rules.
- Proxy fallback only runs when `PROXY_API_TOKEN` is set; empty token = direct only.

## Open questions

- None blocking. Next ops: LIVE scope + confirm `sale_observations` / Telegram on real sales; switch to `enforce` only when monitor looks correct.
