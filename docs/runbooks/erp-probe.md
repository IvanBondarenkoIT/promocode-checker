# ERP coffee sales probe (Stage 4.1)

Validate live Granit coffee sales for practice shop cards **before** wiring promocode auto-close.

Product UI stays English; this runbook is ops English.

## Access modes

| Where | Mode | What you need |
|-------|------|----------------|
| Local / laptop | `ERP_ACCESS_MODE=proxy` | `PROXY_API_URL` + `PROXY_API_TOKEN` (same Proxy API as prices/granit/stock: `POST /api/query`, Bearer) |
| Windows Server prod | `ERP_ACCESS_MODE=direct` | `FIREBIRD_DSN=127.0.0.1/3055:DK_GEORGIA` + readonly `FIREBIRD_USER` / `FIREBIRD_PASSWORD` (same pattern as firebird-db-proxy) |

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

## Local setup

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
FIREBIRD_DSN=127.0.0.1/3055:DK_GEORGIA
FIREBIRD_USER=<readonly>
FIREBIRD_PASSWORD=<secret>
# Proxy optional if direct works:
# PROXY_API_URL=
# PROXY_API_TOKEN=
```

One-shot probe on the server (host Python with repo + venv, or exec into app container if env is injected):

```powershell
cd C:\Projects\promocode-checker
python scripts/probe_erp_coffee_sales.py --day today --out artifacts/erp-probe/
```

Requires Firebird listening on `3055` and `fdb` installed for direct mode.

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

2. Backdate `created_at` so ERP sales for today are after code creation (reconcile requires `created_at ≤ sold_at ≤ now`):

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
