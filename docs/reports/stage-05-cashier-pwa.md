# Stage 05 Cashier PWA Report

## Planned scope

- Cashier PWA: one numeric 8-digit input, absolute autofocus, scanner Enter, 1.5s debounce
- Status colors + Redeem button + audio feedback
- `point_id` from query/settings + session heartbeat without login
- Tests + this stage report
- Do **not** start Stage 6, concurrent redeem lock, or live ERP SQL

## Implementation

- Frontend (Vite + React + TypeScript + PWA):
  - [`frontend/src/cashier/CashierApp.tsx`](../../frontend/src/cashier/CashierApp.tsx)
  - digits-only input, auto-submit on 8 digits / Enter
  - autofocus recovery (blur / visibility / pointer outside buttons)
  - 1.5s lock after API requests (blocks re-scan; Redeem stays available after valid check)
  - status tones: active / used / missing / error
  - audio: success beep / error double buzz (Web Audio API)
  - `point_id` from `?point_id=` → localStorage → `VITE_DEFAULT_POINT_ID`
  - session meta: start time, last activity, heartbeat timestamp
- Backend:
  - `POST /api/v1/cashier/heartbeat` (no login, returns `point_id` + `server_time`)
  - CORS for Vite `localhost:5173`
- Dev: Vite proxies `/api` and `/health` to `http://127.0.0.1:8000`

## Tests

- Backend: `python -m pytest tests/backend -v` → **29 passed** (includes heartbeat)
- Frontend: `npm test` in `frontend/` → **8 passed**
  - logic/point_id unit tests
  - CashierApp: digits filter, auto-submit + redeem enable, 1.5s lock
- Frontend build: `npm run build` → ok (PWA service worker generated)

## Review notes

- Stage 5 must-haves from supervisor gate are covered.
- No cashier login; point binding via URL/query.
- Manual hardware scanner check still recommended on RDP target before Stage 7.

## Risks and follow-ups / open questions

1. Concurrent redeem row-lock still deferred (after Stage 5, per gate).
2. Live Granit SQL validation remains Stage 4.1.
3. Heartbeat is connectivity ping only — no persisted cashier_sessions table yet (admin Stage 6 may need it).
4. Static frontend serving from FastAPI/Docker is Stage 8; local now uses Vite `:5173` + API `:8000`.
5. Before Stage 6: confirm admin route should be separate Vite app entry vs shared router.
