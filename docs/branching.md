# Branching Strategy

## Main branches

| Branch | Environment | Deploy |
|--------|-------------|--------|
| `develop` | local / integration | CI only (lint + tests) |
| `railway-demo` | Railway demo | Railway native GitHub deploy + [`infra/railway.toml`](../infra/railway.toml) |
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
5. Promote to `railway-demo` when demo needs update.
6. Merge validated production-ready changes into `main`.

## CI mapping (Stage 9)

GitHub Actions [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on `push` and `pull_request` to `develop`, `railway-demo`, and `main`:

- backend: `ruff` + `pytest` with Postgres service
- frontend: `npm test` + `npm run build`

Deploy is **not** done by Actions in Stage 9:

- Railway watches `railway-demo` via project GitHub connection
- Production stays manual/server Docker from `main`

## Notes

- Do not skip stage reports.
- Keep branch names short and readable.
- Do not force-push `main`.
