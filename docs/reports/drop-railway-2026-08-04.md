# Drop Railway — local + server-prod only (2026-08-04)

## Scope

Remove Railway as a delivery target. Environments are **local** and **server-prod**. General / acceptance testing runs on the Windows Server Docker stack.

## Changes

| Area | Action |
|------|--------|
| Assets | Deleted `railway.toml`, `infra/railway.toml`, `infra/railway.env.example`, `docs/runbooks/railway.md` |
| CI | `.github/workflows/ci.yml` — `develop` + `main` only |
| Code | Removed `RAILWAY_PUBLIC_DOMAIN` / CORS hook |
| Docs | `decisions`, `env-matrix`, `branching`, `AGENTS`, handoff, runbooks, prompts, plan |
| Server | General smoke checklist in `docs/runbooks/server-prod.md` |
| Tests | `test_railway_config_present` → `test_prod_compose_health_endpoint` |

Kept: `postgres://` URL normalization (generic).

## Owner ops

- Disconnect/delete Railway project if present
- Optionally delete remote GitHub branch `railway-demo`

## Verification

```powershell
python -m pytest tests/infra/test_deploy_assets.py tests/backend/test_config_database_url.py -q
```
