# Stage 06 Admin UI Report

## Planned scope

- Same Vite app, route `/admin` + login from env credentials
- Roles `admin` / `viewer` (viewer read-only)
- Dashboard stats + table browsers for checker DB tables
- Admin controlled edits with audit trail (USED→ACTIVE, fraud review)
- Tests + stage report + commit/push

## Implementation

### Backend

- Auth: signed bearer tokens via [`backend/app/core/admin_auth.py`](../../backend/app/core/admin_auth.py) + `APP_SECRET_KEY`
- API [`backend/app/api/v1/admin.py`](../../backend/app/api/v1/admin.py):
  - `POST /api/v1/admin/login`
  - `GET /api/v1/admin/me`, `/dashboard`, `/tables/{name}`
  - `PATCH /api/v1/admin/promocodes/{id}` (admin only, audit)
  - `PATCH /api/v1/admin/fraud-warnings/{id}` (admin only, audit)
- Services: dashboard, table listing, mutations + [`admin_audit.py`](../../backend/app/services/admin_audit.py)

### Frontend

- React Router in [`frontend/src/App.tsx`](../../frontend/src/App.tsx): `/` cashier, `/admin/*` admin
- Admin pages under [`frontend/src/admin/`](../../frontend/src/admin/):
  - login, dashboard, table browser + inline edit form (admin)
  - session in `localStorage`
- Styles: [`frontend/src/styles/admin.css`](../../frontend/src/styles/admin.css)

## Tests

- Backend: `python -m pytest tests/backend -v` → **36 passed**
  - `test_admin_auth_unit.py`, `test_admin_api.py`
- Frontend: `npm test` → **10 passed**
  - admin login form + cashier suite still green

## Manual check

```powershell
uvicorn app.main:app --app-dir backend --reload
cd frontend && npm run dev
# Cashier: http://localhost:5173/?point_id=shop_01
# Admin:   http://localhost:5173/admin/login
# creds from .env: ADMIN_* / VIEWER_*
```

## Review notes

- Stage 6 MVP: table edit UI is row-select + status/reason form (not full inline grid editor).
- Viewer can browse dashboard/tables; mutations return 403.

## Risks and follow-ups / open questions

1. Token stored in localStorage — acceptable for internal admin MVP; consider httpOnly cookie in Stage 8 prod hardening.
2. No paginated UI controls yet (API supports offset; UI loads first page).
3. Stage 7 desktop wrapper next; static serve from FastAPI still Stage 8.
