# Branching Strategy

## Main branches

- `develop` - primary development branch.
- `railway-demo` - demonstration branch for Railway deployment.
- `main` - stable production branch for Windows Server Docker deployment.

## Feature branches

Use one branch per focused task:

- `feature/bootstrap-repo`
- `feature/backend-core`
- `feature/erp-reconcile`
- `feature/frontend-pwa`
- `feature/admin-ui`
- `feature/desktop-shell`
- `feature/deploy-cicd`

## Flow

1. Start from `develop`.
2. Implement one stage or sub-stage in a `feature/*` branch.
3. Run the relevant tests for that stage.
4. Do a short stage review and write a brief report into `docs/reports/`.
5. Merge into `develop` only after the stage gate is closed.
6. Promote selected changes into `railway-demo` for showcase deployment.
7. Merge validated production-ready changes into `main`.

## Notes

- Do not skip stage reports.
- Do not mix infrastructure, UI, and ERP logic in one branch unless the task truly requires it.
- Keep branch names short and readable so the deployment history is easy to understand.
