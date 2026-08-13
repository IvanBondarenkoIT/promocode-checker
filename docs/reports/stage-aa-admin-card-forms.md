# Stage AA — Admin customer card list + element forms (2026-08-13)

## Scope

Give admins full control over individual customer cards (`promocodes`): list page, create/edit element forms, reactivate (USED→ACTIVE), delete with audit. Viewer remains read-only. English UI only. Local-first.

## Delivered

| Area | Paths |
|------|-------|
| API | `GET/POST /api/v1/admin/promocodes`, `GET .../defaults`, `GET/PATCH/DELETE .../{id}` |
| Service | [`backend/app/services/admin_promocodes.py`](../../backend/app/services/admin_promocodes.py) |
| Schemas | Extended patch + create/delete/detail/defaults in [`admin.py`](../../backend/app/schemas/admin.py) |
| UI list | `/admin/cards` — [`AdminCardsListPage.tsx`](../../frontend/src/admin/AdminCardsListPage.tsx) |
| UI form | `/admin/cards/new`, `/admin/cards/:id` — [`AdminCardFormPage.tsx`](../../frontend/src/admin/AdminCardFormPage.tsx) |
| Dashboard | Primary **Customer cards** link |
| Tests | `tests/backend/test_admin_api.py`, `frontend/src/admin/AdminCardsPages.test.tsx` |

## Create defaults

- Prefers ACTIVE campaign matching `active_campaign_kind`
- Status `ACTIVE`, `expires_at` = now + `PROMOCODE_TTL_DAYS`
- Empty promocode / ERP id; `customer_card` copies promocode when left blank

## Verification

- `pytest tests/backend/test_admin_api.py` — 5 passed
- `vitest` AdminCardsPages + AdminLoginPage — 5 passed

## Local test checklist

1. Admin → Customer cards → Add card (defaults filled)
2. Save ORGN + 8–20 digit code
3. Open → USED → ACTIVE (reactivate)
4. Edit name/phone/expires; check `admin_audit_logs`
5. Delete with reason
6. Viewer: no Add/Save/Delete

## Open questions

- None blocking.
