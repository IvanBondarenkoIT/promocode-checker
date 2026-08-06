# Stage V — Pre-production: segment, campaigns, data scope (2026-08-06)

## Scope

Issue promocodes to a real customer segment, keep rehearsal data and real data
strictly apart, and rehearse the go-live flow locally before touching the server.

## Delivered

| Area | Paths |
|------|-------|
| Migration | `005_campaign_scope` — `campaigns.kind` / `code_prefix`, `promocodes` customer fields + `uq_promocodes_campaign_customer`, `app_settings` |
| Scope | `backend/app/services/campaign_scope.py` (single enforcement point) |
| Cashier | `OUT_OF_SCOPE` result, campaign kind in response, `TEST MODE` badge |
| Reconcile | scope filter + `CLOSED` campaigns skipped, fraud leg scoped |
| Segment import | `backend/app/services/segment_import.py`, `scripts/import_segment_promocodes.py` (dry-run, rollback, issued CSV) |
| Generation | `generate_unique_promocode(prefix=..., reserved=...)` |
| Admin API | `GET/PUT /api/v1/admin/scope`, table filters (`campaign_code`, `kind`, `status`, `search`) + pagination |
| Admin UI | `ScopeSwitch` on the dashboard, filters and Previous/Next on tables |
| Telegram | `campaign_import`, `scope_switched`, campaign lines in the daily digest |
| Docs | `runbooks/campaign-scope.md`, `runbooks/preprod-calibration.md`, rewritten `runbooks/campaign-import.md` |

## Decisions applied

- Campaign `kind` is fixed at creation; import refuses to flip it or to change a prefix once codes exist.
- Promocodes without a campaign count as `TEST` and are never served in `LIVE`.
- `expires_at` follows `campaigns.ends_at` when set, otherwise TTL.
- One code per customer per campaign (DB constraint, not just app logic).
- Code prefixes: `5` segment, `6` calibration, `9` new tests, `1`–`4` legacy demos.

## Local run (2026-08-06)

Segment `data/input/coffee_beans_1_2_kg_12m.csv` — 175 customers, 0 file errors.

| Step | Result |
|------|--------|
| Dry-run import | 175 codes previewed, nothing written, campaign not created |
| Real import | 175 issued, export `artifacts/campaigns/beans_1_2kg_preprod_issued_*.csv` |
| Scan in `TEST` scope | `out_of_scope`, code stayed `ACTIVE` |
| Redeem in `TEST` scope | `out_of_scope`, no close |
| Scan in `LIVE` scope | `valid`, campaign shown |
| Mock coffee sale + reconcile | `AUTO_CLOSE`, code `USED`, alert with product, `45.00 ₾`, order and prior scan |
| Re-import | 175 skipped, no duplicate codes |

Tests: `70 passed` backend (8 new in `tests/backend/test_campaign_scope.py`), `16 passed` frontend, ruff clean, frontend build OK.

Fixed on the way: `test_telegram_dedup` counted every notification row, so it failed
whenever pytest-randomly put a committing test first; it now filters by its own dedup key.

## Still missing for a real launch

1. **Delivery channel for the codes.** The export CSV exists, but nobody sends it yet (SMS/Telegram/print). Owner decision.
2. **Staff card ERP ids.** `data/input/staff_cards.csv` is not filled — calibration cannot run until we know the `ORGN.ID` of our shop cards.
3. **Auto-close without a scan.** A customer who buys coffee without showing the code still gets it closed. Current behaviour is intentional but should be confirmed by the owner before launch.
4. **Server rollout.** Migration 005 + import + scope switch, backup first — see `runbooks/server-prod.md`.
5. **PII retention.** Names and phones now live in `promocodes`; no purge policy yet.
6. **Prod stack on this machine** (`promocode-checker-prod-*`) still runs the pre-005 image; it must be rebuilt before its DB is migrated.

## Note on the local dev database

`tests/backend/conftest.py` drops and recreates all tables for the session. Running the
suite wipes the dev DB, which is what kept killing the Telegram bot poll with
`relation "telegram_bot_state" does not exist`. Re-run `scripts/run_migrations.py`
after tests before starting the poll.
