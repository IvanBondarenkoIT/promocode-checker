# Branching Strategy

## Main branches

| Branch | Environment | Deploy |
|--------|-------------|--------|
| `develop` | local / integration | CI only (lint + tests) |
| `main` | Windows Server production | Docker Compose on server (`infra/docker-compose.prod.yml`); no force-push |

## Feature branches

Use one branch per focused task, for example:

- `feature/cicd`
- `feature/admin-ui`
- `feature/deploy`

## Flow

1. Start from `develop`.
2. Implement one stage in a `feature/*` branch.
3. Run tests; write `docs/reports/stage-XX-....md`.
4. Commit on `feature/*`, merge into `develop`, push both.
5. After local verification, merge validated production-ready changes into `main`.
6. On the server: pull `main` and run general smoke — [runbooks/server-prod.md](runbooks/server-prod.md).

## CI mapping

GitHub Actions [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on `push` and `pull_request` to `develop` and `main`:

- backend: `ruff` + `pytest` with Postgres service
- frontend: `npm test` + `npm run build`

Deploy is **not** done by Actions:

- Production stays manual/server Docker from `main`

## Notes

- Do not skip stage reports.
- Keep branch names short and readable.
- Do not force-push `main`.
- Branch `railway-demo` is retired (Railway dropped 2026-08-04); delete remote branch if it still exists.
