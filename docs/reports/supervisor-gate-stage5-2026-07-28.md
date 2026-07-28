# Supervisor Gate — Stage 5 Approval — 2026-07-28

## Purpose

Close the three product gate questions from the supervisor audit and explicitly approve Stage 5 Cashier PWA.

## Gate answers (locked)

| # | Question | Decision |
|---|----------|----------|
| 1 | Accept Stage 4 without live ERP SQL yet? | **Yes** — Stage 4 closed for local/mock; live SQL = Stage 4.1 follow-up |
| 2 | Concurrent redeem lock when? | **After Stage 5 PWA** |
| 3 | Telegram auto-close mode? | **One summary per reconcile run** |

Source of defaults: Recommended options from supervisor plan `Supervisor audit now`, applied when implementing the gate (owner accepted the plan to execute).

## Related locked notes

- Discount marker not required yet: whitelist coffee sale in window is enough until live ERP SQL is validated.
- Env `COFFEE_BEANS_GROUP_IDS` remains runtime source of truth; `config/coffee_beans_groups.json` is documentation/config mirror.

## Stage 5 status

**APPROVED to start.**

Implementation agent may begin Stage 5 Cashier PWA under stage-gate rules.

Must-haves:

- one numeric input, length 8
- absolute autofocus recovery
- scanner Enter auto-submit
- 1.5s debounce lock
- status colors + Redeem button
- audio feedback
- `point_id` from query/settings
- session heartbeat without login
- tests/manual checks + `docs/reports/stage-05-cashier-pwa.md`

Do **not** start Stage 6+ in the same pass.

## After Stage 5

Supervisor must re-check Stage 5 report before Stage 6.
Then schedule: concurrent redeem lock + optional Stage 4.1 live ERP SQL validation.
