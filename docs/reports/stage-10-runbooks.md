# Stage 10 Runbooks Report

## Scope

- Complete local / Railway / server-prod runbooks
- Finalize env matrix against `.env.example` and deploy examples
- Employee cashier launch instructions (bilingual steps; English-only UI labels)
- Wire INDEX / AGENTS / handoff / plan / prompts / README / supervisor

## Implementation

| Path | Role |
|------|------|
| [`docs/runbooks/README.md`](../runbooks/README.md) | Index + env map |
| [`docs/runbooks/local.md`](../runbooks/local.md) | Dev split + Docker stack + troubleshooting |
| [`docs/runbooks/railway.md`](../runbooks/railway.md) | `railway-demo` deploy / smoke |
| [`docs/runbooks/server-prod.md`](../runbooks/server-prod.md) | Windows Server Docker + RDP desktop |
| [`docs/runbooks/employee-cashier.md`](../runbooks/employee-cashier.md) | Cashier guide (RU steps, EN UI) |
| [`docs/env-matrix.md`](../env-matrix.md) | Full variable matrix |

Status docs updated: `AGENTS.md`, `docs/context-handoff.md`, `docs/plan/IMPLEMENTATION_PLAN.md`, `docs/INDEX.md`, `docs/prompts/stage-prompts.md`, `docs/supervisor.md`, `README.md`, `.cursor/rules/promocode-checker.mdc`, top link in `docs/local-development.md`.

## Verification

- Relative links from `docs/INDEX.md` → `runbooks/*` → `infra/*.example`, `desktop/README.md`, Stage 8/9 reports, `branching.md`
- Employee guide uses real cashier labels: `Shop`, `Ready`, `Apply discount`, `ACTIVE` / `USED` / `EXPIRED` / `NOT FOUND` / `APPLIED` / `ERROR`
- Explicit English-only UI callout in employee + runbook README

No application code changes in this stage.

## Review notes

- Ops runbooks English; employee sheet bilingual as planned
- Implementation plan stages 1–10 are complete; remaining items are deferred follow-ups

## Risks / follow-ups / open questions

1. Confirm Railway GitHub connection to `railway-demo` in the live Railway project.
2. Stage 4.1 live Granit SQL still deferred.
3. Server TLS / Caddy still optional.
4. Optional GHCR publish still deferred.

## Open questions

- None blocking stage close.
