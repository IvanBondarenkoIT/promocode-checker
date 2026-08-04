# Stage 4.1 — ERP coffee sales probe

## Scope

- Align live Granit coffee-sales SQL with ORGN / STORZAKAZDT / STORZDTGDS / GOODS
- Add practice shop-card catalog (ORGN IDs)
- Probe CLI writing CSV/JSON under `artifacts/erp-probe/`
- Document local=proxy vs server-prod=direct
- Unit tests for query builder + mock probe
- After owner CSV OK: live AUTO_CLOSE demo via reconcile

## Implementation

| Path | Role |
|------|------|
| [`config/test_shop_cards.json`](../../config/test_shop_cards.json) | 14 unique practice ORGN cards |
| [`backend/app/integrations/erp/queries.py`](../../backend/app/integrations/erp/queries.py) | Granit SQL + paid statuses + string `sold_at` parse |
| [`backend/app/integrations/erp/proxy.py`](../../backend/app/integrations/erp/proxy.py) | Naive `YYYY-MM-DD HH:MM:SS` params (Firebird-safe) |
| [`scripts/probe_erp_coffee_sales.py`](../../scripts/probe_erp_coffee_sales.py) | Probe CLI |
| [`docs/runbooks/erp-probe.md`](../runbooks/erp-probe.md) | How to run / read CSV / AUTO_CLOSE demo |
| `.env.example` / `infra/.env.prod.example` | proxy local; direct Firebird prod template |

## Verification

```powershell
python -m pytest tests/backend/test_erp_queries.py tests/backend/test_probe_erp_coffee_sales.py -q
python scripts/probe_erp_coffee_sales.py --mode mock --out artifacts/erp-probe/
```

### Live proxy probe (2026-08-04)

Owner OK on CSV. Shop cards with coffee that day: **21470** (4), **12523** (2), **14661** (2), **17306** (1) — 9 lines total.

### Live AUTO_CLOSE demo (same day)

1. Imported ACTIVE codes `41000001`–`41000004` for those four ORGN IDs (campaign `auto_close_demo`).
2. Backdated `created_at` to `2026-08-03` so today’s ERP sales fall in the match window (`created_at ≤ sold_at ≤ now`).
3. `python scripts/run_reconcile.py` with `ERP_ACCESS_MODE=proxy`:

```text
reconcile ok auto_closed=4 fraud_warnings=1
auto_closed: 41000001, 41000002, 41000003, 41000004
```

4. DB check: all four `USED`; `checker_logs` rows `AUTO_CLOSE` / `point_id=reconcile` / `erp_sale_matched=true`.

(The extra `fraud_warnings: 10000003` is from an older MANUAL_CLOSE dummy seed — unrelated to the demo codes.)

## Review notes

- Draft DOCHEAD/DOCLINE/CLIENTS SQL removed from the live path
- Reconcile uses the same adapter/SQL as the probe
- Empty shop-card days are OK

## Risks / follow-ups / open questions

1. Server-prod: set `ERP_ACCESS_MODE=direct` + Firebird creds; optional one-shot probe on server.
2. Ensure `fdb` available in prod image/host for direct mode.
3. Campaign import: remember to backdate `created_at` when demoing against sales that already happened today.

## Open questions

- None blocking Stage 4.1 close.
