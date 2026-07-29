# Stage 09 CI/CD Report

## Planned scope

- GitHub Actions lint/tests for backend + frontend
- Branch → environment mapping (`develop` / `railway-demo` / `main`)
- Document Railway/prod deploy as native GitHub/Railway + server Docker (no GHCR publish in this stage)
- Fix stale Stage 5.1 supervisor checkbox / INDEX blurb
- Stage report + status doc updates

## Implementation

- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
  - triggers: `push` + `pull_request` on `develop`, `railway-demo`, `main`
  - **backend** job: Python 3.11, Postgres 15 service on `:5432`, `ruff check .`, `pytest tests/backend -v`
  - **frontend** job: Node 20, `npm ci`, `npm test`, `npm run build`
- [`docs/branching.md`](../branching.md) — CI/deploy mapping table
- Doc hygiene: Stage 5.1 supervisor checkbox marked done; INDEX supervisor line updated

Deploy wiring (Stage 9 choice):

- Railway demo: continue via Railway GitHub connection on `railway-demo` + existing `infra/railway.toml`
- Production: server Docker from `main` (manual compose), not Actions deploy

## Tests

Local (Docker Desktop unavailable this run):

- `ruff check .` → passed
- `pytest tests/backend` → **15 passed, 27 skipped** (Postgres not reachable on `:5433`)
- `frontend`: `npm test` → **13 passed**; `npm run build` → ok

CI expectation: backend service Postgres makes integration tests run (not skip) on GitHub-hosted runners.

## Review notes

- Stage 9 quality gate is in place for the three long-lived branches.
- Image publish / Actions→Railway token deploy intentionally deferred; native Railway + server compose remain the deploy paths from Stage 8.
- Stages 1–8 remain closed; no product feature work in this stage.

## Risks and follow-ups / open questions

1. Confirm Railway project is connected to `railway-demo` after first push of CI files.
2. Stage 10: finalize employee/runbook docs and env matrix polish.
3. Re-run full backend suite locally when Docker Desktop is up, to mirror CI before merge if desired.
4. Optional later: GHCR image build on `main` if server pulls from registry instead of build-on-host.
