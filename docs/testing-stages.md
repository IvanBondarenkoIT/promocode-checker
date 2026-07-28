# Testing by Stage

## Rule

Each stage must end with:

1. Relevant tests or verification commands.
2. Short review of the result.
3. A brief markdown report with completed work, risks, and follow-up questions.

## Stage 1

- Verify Python version.
- Create and activate `.venv`.
- Install backend dependencies.
- Run the FastAPI health endpoint.
- Confirm the repo structure and env template are present.

## Stage 2

- Run database migrations on local PostgreSQL.
- Verify schema, indexes, enums, and constraints.
- Add focused tests for promo validation and core models.

## Stage 3

- Test `check`, `redeem`, and barcode endpoints.
- Validate log creation and response payloads.
- Confirm cashier flow speed and correctness under normal repeated use.

## Stage 4

- Test ERP adapter using a mock provider.
- Run reconcile job against sample data.
- Validate auto-close, matched sale flags, and fraud warnings.
- Verify Telegram notifications for changes and failures.

## Stage 5

- Test scanner-style input flow.
- Verify numeric-only input, debounce, autofocus, and audio signals.
- Validate multi-user concurrency at the application level.

## Stage 6

- Test admin and viewer access rules.
- Verify audit trail for manual edits.
- Validate dashboards, filters, and report visibility.

## Stage 7

- Test desktop shell launch under RDP.
- Verify point binding and fullscreen-friendly behavior.

## Stage 8

- Build and run Docker locally.
- Validate Railway demo configuration.
- Verify healthchecks and restart policies.

## Stage 9

- Validate CI runs on pull requests.
- Verify deployment mapping for `develop`, `railway-demo`, and `main`.
