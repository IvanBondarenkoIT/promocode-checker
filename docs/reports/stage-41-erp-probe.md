# Stage 4.1 — ERP coffee sales probe

## Scope

- Align live Granit coffee-sales SQL with ORGN / STORZAKAZDT / STORZDTGDS / GOODS
- Add practice shop-card catalog (ORGN IDs)
- Probe CLI writing CSV/JSON under `artifacts/erp-probe/`
- Document local=proxy vs server-prod=direct
- Unit tests for query builder + mock probe

**Out of scope until owner OK on probe CSV:** full promocode↔sale reconcile auto-close validation with live data.

## Implementation

| Path | Role |
|------|------|
| [`config/test_shop_cards.json`](../../config/test_shop_cards.json) | 14 unique practice ORGN cards |
| [`backend/app/integrations/erp/queries.py`](../../backend/app/integrations/erp/queries.py) | Granit SQL + paid statuses + optional `--all-coffee` FIRST n |
| [`backend/app/integrations/erp/types.py`](../../backend/app/integrations/erp/types.py) | Optional `customer_name`, `order_id` on matches |
| [`scripts/probe_erp_coffee_sales.py`](../../scripts/probe_erp_coffee_sales.py) | Probe CLI (`--mode mock` / settings / `--all-coffee`) |
| [`docs/runbooks/erp-probe.md`](../runbooks/erp-probe.md) | How to run and read CSV |
| `.env.example` / `infra/.env.prod.example` | proxy local; direct Firebird prod template |
| `tests/backend/test_erp_queries.py` / `test_probe_erp_coffee_sales.py` | Unit coverage |

`ERP_PAID_STATUSES` (default `1,2,3,5`) added to Settings; proxy/direct adapters pass it into the query builder.

## Verification

```powershell
python -m pytest tests/backend/test_erp_queries.py tests/backend/test_probe_erp_coffee_sales.py tests/backend/test_erp_mock_adapter.py -q
python scripts/probe_erp_coffee_sales.py --mode mock --out artifacts/erp-probe/
```

Live proxy probe (owner):

```powershell
# .env: ERP_ACCESS_MODE=proxy + PROXY_API_TOKEN
python scripts/probe_erp_coffee_sales.py --day today --customers config/test_shop_cards.json
```

## Review notes

- Draft DOCHEAD/DOCLINE/CLIENTS SQL removed from the live path
- Reconcile job already uses `get_erp_adapter()` → same SQL once env points at proxy/direct
- Do not treat empty shop-card days as failures

## Risks / follow-ups / open questions

1. Owner visual OK on real proxy CSV for today.
2. After OK: optional seed ACTIVE promocodes with `customer_erp_id` from cards that sold coffee → `run_reconcile` AUTO_CLOSE demo.
3. Confirm `CSDTKTHBID` paid status list on live data if probe returns zero rows unexpectedly.
4. Server: install `fdb` in prod image / host if using `ERP_ACCESS_MODE=direct`.

## Open questions

- None blocking stage close for the probe deliverable; live CSV review is the next human gate.
