# Desktop wrapper (Stage 7)

Lightweight Windows launcher for RDP cashiers. Opens the cashier PWA in a dedicated app window (Edge/Chrome app mode) with a fixed `point_id` — no browser tabs or address bar friction.

## Setup

1. Copy config:

```powershell
cd D:\CursorProjects\promocode-checker\desktop
Copy-Item config.example.json config.json
```

2. Edit `config.json`:

| Field | Description |
|-------|-------------|
| `cashierBaseUrl` | Cashier UI base URL (prod: your server URL) |
| `pointId` | Shop / point identifier passed as `?point_id=` |
| `fullscreen` | Start in fullscreen app mode |
| `browser` | `auto`, `edge`, or `chrome` |

3. Ensure backend + frontend (or prod static) are running.

## Launch

```powershell
.\launch-cashier.ps1
```

Optional override for one-off testing:

```powershell
.\launch-cashier.ps1 -PointId shop_02 -CashierBaseUrl http://127.0.0.1:5173
```

## RDP deployment notes

- Pin `launch-cashier.ps1` shortcut on the cashier desktop.
- Set `pointId` per machine or per shortcut (one config per shop).
- Prefer `cashierBaseUrl` pointing to the server-prod Docker host, not localhost, on real RDP sessions.
- Test hardware scanner (keyboard wedge + Enter) in app mode before go-live.

## UI language

English only — same as the web cashier PWA.
