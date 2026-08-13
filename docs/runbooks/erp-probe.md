# ERP coffee sales probe (Stage 4.1)

Validate live Granit coffee sales for practice shop cards **before** wiring promocode auto-close.

Product UI stays English; this runbook is ops English.

## Access modes

| Where | Mode | What you need |
|-------|------|----------------|
| Local / laptop (proxy) | `ERP_ACCESS_MODE=proxy` | `PROXY_API_URL` + `PROXY_API_TOKEN` |
| Local / laptop (GDB copy) | `ERP_ACCESS_MODE=direct` | File DSN + `FIREBIRD_LIBRARY_PATH` to FB 2.5 `fbembed.dll` (see below) |
| Windows Server prod | `ERP_ACCESS_MODE=direct` | `FIREBIRD_DSN=host.docker.internal/3050:C:/db/GEORGIA.GDB` + same user as local Firebird proxy; optional proxy fallback |

Paid order statuses default: `ERP_PAID_STATUSES=1,2,3,5`.  
Coffee groups (locked): `COFFEE_BEANS_GROUP_IDS=11077,16276,16279`.

## Test shop cards

Catalog: [`config/test_shop_cards.json`](../../config/test_shop_cards.json).

These are **ORGN customer IDs** (practice clients), not promocode values. Later reconcile will match `promocodes.customer_erp_id` to the same IDs.

| ORGN ID | Name |
|---------|------|
| 12523 | КЛИЕНТ PALIASHVILI |
| 21470 | КЛИЕНТ DK BATUMI |
| 18961 | КЛИЕНТ CITYMALL |
| 14661 | BATUMI MALL |
| 17306 | КЛИЕНТ EAST POINT |
| 18957 | lali machaidze |
| 27541 | Алла |
| 28383 | zanda |
| 28590 | marya |
| 28591 | heand shot |
| 28600 | daniyel |
| 29067 | mariam jashiashvili |
| 29077 | Giorgi Abashishvili |
| 29079 | Isabelle Noulard |

## Local direct (GDB file copy)

For offline validation against `GEORGIA.GDB` (ODS 11 — needs Firebird 2.5 embedded, not FB 5.0 server):

```env
ERP_ACCESS_MODE=direct
FIREBIRD_DSN=D:\CursorProjects\DB-copy\GEORGIA.GDB
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey
FIREBIRD_LIBRARY_PATH=D:\CursorProjects\granit-clients-based-segmentation\tools\firebird25\embedded\fbembed.dll
```

```powershell
pip install -e ".[erp-direct]"
python scripts/probe_erp_direct.py --customer-ids 21470,12523 --days 30
```

Read-only: prints engine version + coffee sales table; no DB writes, no Telegram.

## Local setup (proxy)

1. Copy `.env.example` → `.env` (repo root).
2. Set:

```env
ERP_ACCESS_MODE=proxy
PROXY_API_URL=http://178.63.72.227:8010
PROXY_API_TOKEN=<token from Proxy API / parallel project>
ERP_PAID_STATUSES=1,2,3,5
COFFEE_BEANS_GROUP_IDS=11077,16276,16279
APP_TIMEZONE=Asia/Tbilisi
```

3. Activate venv and run (no checker Postgres required for proxy probe):

```powershell
cd D:\CursorProjects\promocode-checker
.\.venv\Scripts\Activate.ps1
python scripts/probe_erp_coffee_sales.py --day today --customers config/test_shop_cards.json --out artifacts/erp-probe/
```

Dry / CI path (no network):

```powershell
python scripts/probe_erp_coffee_sales.py --mode mock --out artifacts/erp-probe/
```

Optional:

```powershell
# Subset of ORGN IDs
python scripts/probe_erp_coffee_sales.py --customer-ids 12523,21470

# Any coffee lines that day (capped)
python scripts/probe_erp_coffee_sales.py --all-coffee --limit 500
```

## Outputs

Under `artifacts/erp-probe/` (gitignored):

- `coffee_sales_YYYY-MM-DD.csv` — `customer_erp_id`, `customer_name`, `sold_at`, `group_id`, `product_name`, `order_id`
- `coffee_sales_YYYY-MM-DD.json` — same payload for tooling

Console prints total lines and counts per shop card.

## How to read the CSV

1. Confirm group IDs are only coffee whitelist values.
2. Confirm shop cards you expect to have sold coffee today appear with plausible `sold_at` (Asia/Tbilisi calendar day).
3. Empty day for a card is OK (no practice sale).
4. **Do not** run full promocode↔sale reconcile / auto-close until this file looks right.

## Server prod (direct)

In `infra/.env.prod` (never commit secrets):

```env
ERP_ACCESS_MODE=direct
FIREBIRD_DSN=host.docker.internal/3050:C:/db/GEORGIA.GDB
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=<same as C:\FirebirdAPI\firebird-db-proxy\.env DB_PASSWORD>
FIREBIRD_LIBRARY_PATH=
# Optional fallback if direct fails (local proxy on the same host, usually :8000):
PROXY_API_URL=http://host.docker.internal:8000
PROXY_API_TOKEN=
```

Compose adds `extra_hosts: host.docker.internal:host-gateway` so the Linux container reaches Firebird on the Windows host.

**Do not** use `127.0.0.1` inside the container — that points at the container itself.

Probe from the server (preferred):

```powershell
cd C:\Projects\promocode-checker\desktop
.\check-erp.ps1
.\check-erp.ps1 -CustomerIds "21470,12523,14661,17306" -Days 30
```

Expect `Engine version: ...` and sales lines (or empty window). If connect fails with *Connection refused* / `-902`, check Firebird on port **3050** (same as the working proxy `DB_PORT`) and whether docker bridge IPs are allowed in Firebird whitelist. Do not put `C:\db\GEORGIA.GDB` in `FIREBIRD_LIBRARY_PATH`.

Legacy CSV probe (still works):

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml exec reconcile `
  python /app/scripts/probe_erp_coffee_sales.py --day today --customers config/test_shop_cards.json
```

## SQL shape (reference)

Live query uses Granit tables: `ORGN`, `STORZAKAZDT`, `STORZDTGDS`, `GOODS` (`OWNER` = group). See `backend/app/integrations/erp/queries.py`.

## Related

- Env matrix: [`../env-matrix.md`](../env-matrix.md)
- Stage report: [`../reports/stage-41-erp-probe.md`](../reports/stage-41-erp-probe.md)
- Server deploy: [`server-prod.md`](server-prod.md)

## After CSV OK — AUTO_CLOSE demo

1. Import ACTIVE codes for shop cards that had coffee today (promocode = loyalty card, 8–20 digits):

```powershell
# artifacts/auto_close_demo.csv: customer_erp_id,promocode
python scripts/import_campaign_promocodes.py --file artifacts/auto_close_demo.csv --campaign-code auto_close_demo --campaign-name "AUTO_CLOSE demo"
```

2. Same-calendar-day ERP sales now match without backdating `created_at`. Backdate only if you need **previous** days:

```sql
UPDATE promocodes
SET created_at = TIMESTAMPTZ '2026-08-03 00:00:00+00'
WHERE promocode IN ('41000001','41000002','41000003','41000004');
```

3. Run:

```powershell
python scripts/run_reconcile.py
```

4. Expect `auto_closed: …` and `checker_logs.action_type = AUTO_CLOSE` with `erp_sale_matched = true`.
