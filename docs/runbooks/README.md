# Runbooks — Promocode Checker

Operational guides for local development, Windows Server production, and cashier employees.

**Product UI language:** English only (cashier, admin, desktop). Runbooks may use Russian for staff steps; on-screen labels stay English.

## Environments

| Env | Branch | Guide |
|-----|--------|-------|
| Local | `develop` | [local.md](local.md) |
| Server prod (RDP) | `main` | [server-prod.md](server-prod.md) — deploy + **general smoke / regression** |

## Employees

- [employee-cashier.md](employee-cashier.md) — how to open the cashier app and redeem a promocode

## Campaigns

- [campaign-import.md](campaign-import.md) — segment import (generated codes) and wave import
- [campaign-scope.md](campaign-scope.md) — global TEST / LIVE switch
- [enforcement-modes.md](enforcement-modes.md) — monitor vs enforce auto-close
- [preprod-calibration.md](preprod-calibration.md) — auto-close rehearsal on shop cards

## ERP probe

- [erp-probe.md](erp-probe.md) — Stage 4.1 coffee sales CSV via Proxy (local) or direct Firebird (server)

## Telegram

- [telegram-alerts.md](telegram-alerts.md) — ops alert bot (not customer barcode bot)

## Related

- Env variables: [`../env-matrix.md`](../env-matrix.md)
- Coffee whitelist text: [`../coffee-beans-whitelist.txt`](../coffee-beans-whitelist.txt)
- Branch / CI / deploy: [`../branching.md`](../branching.md)
- Deploy report: [`../reports/stage-08-deploy.md`](../reports/stage-08-deploy.md)
- CI report: [`../reports/stage-09-cicd.md`](../reports/stage-09-cicd.md)
- Desktop launcher: [`../../desktop/README.md`](../../desktop/README.md)
- Prod update script: [`../../desktop/update-prod.ps1`](../../desktop/update-prod.ps1)
- Detailed local setup: [`../local-development.md`](../local-development.md)
