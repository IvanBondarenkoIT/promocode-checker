# Stage 03 Cashier API Report

## Planned scope

- add cashier API endpoints for `check`, `redeem`, and barcode image
- write `checker_logs` for scan/check and manual close
- validate response payloads with backend tests
- add a local seed script for demo promocodes

## Implementation

- Schemas: `backend/app/schemas/cashier.py`
- Services:
  - `backend/app/services/cashier.py` (`check_promocode`, `redeem_promocode`)
  - `backend/app/services/barcode.py` (Code128 PNG)
- API:
  - `POST /api/v1/cashier/check`
  - `POST /api/v1/cashier/redeem`
  - `GET /api/v1/cashier/barcode/{code}`
- DB session `get_db` now commits on success / rolls back on error
- Seed: `scripts/seed_promocodes.py`

## Behavior notes

- `check` writes `SCAN_CHECK` for 8-digit codes (including not found / expired / used)
- `invalid_format` returns without a log row
- `redeem` closes only `ACTIVE` and non-expired codes → `USED` + `MANUAL_CLOSE`
- repeat redeem returns `used` without a second close log
- barcode returns `image/png`; invalid codes → HTTP 422
- no auth yet (Stage 6); `point_id` defaults to `DEFAULT_POINT_ID`

## Tests

- `python -m ruff check .` -> passed
- `python -m pytest tests/backend -v` -> `18 passed`
  - cashier check/redeem/barcode coverage
  - barcode unit tests
  - existing stage 1–2 suite still green

## Review notes

- Stage 3 core deliverables are in place on `feature/cashier-api`.
- Cashier flow is usable via OpenAPI `/docs` and curl/PowerShell examples in local-development docs.

## Risks and follow-ups

- Stage 4 should add ERP reconcile, `AUTO_CLOSE`, fraud warnings, and Telegram alerts.
- Concurrent redeem of the same code is not yet protected with a row lock / unique close constraint.
- Cashier PWA scanner UX remains Stage 5.
