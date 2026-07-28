# Stage 07 Desktop Wrapper Report

## Scope

Lightweight Windows shell for RDP cashiers: fixed `point_id`, app-mode browser launch, fullscreen-friendly.

## Implementation

- [`desktop/launch-cashier.ps1`](../desktop/launch-cashier.ps1) — Edge/Chrome `--app=` launcher with config / CLI overrides
- [`desktop/config.example.json`](../desktop/config.example.json) — `cashierBaseUrl`, `pointId`, `fullscreen`, `browser`
- [`desktop/README.md`](../desktop/README.md) — setup and RDP deployment notes

## Tests

- `tests/desktop/test_desktop_launcher.py` — config schema + launcher script smoke (**38 backend passed** total)

## Manual check (local)

```powershell
# backend + frontend running
cd desktop
Copy-Item config.example.json config.json
.\launch-cashier.ps1 -NoWait
```

Opens cashier in app window with configured `point_id`.

## Risks / follow-ups

1. RDP hardware scanner validation still required on real cashier machines before prod.
2. Prod URL in `config.json` per deployment — Stage 8 static serve + Docker.
3. No auto-update / single-instance lock yet (optional hardening).

## Open questions

- None blocking Stage 8 deploy.
