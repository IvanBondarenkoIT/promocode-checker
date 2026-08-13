"""Local smoke for admin card CRUD + vite pages."""

from __future__ import annotations

from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
env = dotenv_values(ROOT / ".env")
admin_user = env.get("ADMIN_USERNAME", "admin")
admin_pass = env.get("ADMIN_PASSWORD", "change_me_admin")
viewer_user = env.get("VIEWER_USERNAME", "viewer")
viewer_pass = env.get("VIEWER_PASSWORD", "change_me_viewer")
base = "http://127.0.0.1:8000"
errors: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        errors.append(name)


def main() -> int:
    with httpx.Client(base_url=base, timeout=20.0) as client:
        health = client.get("/health")
        check(
            "health",
            health.status_code == 200 and health.json().get("schema") == "ok",
            health.text[:200],
        )

        login = client.post(
            "/api/v1/admin/login",
            json={"username": admin_user, "password": admin_pass},
        )
        check("admin login", login.status_code == 200, str(login.status_code))
        token = login.json()["token"] if login.status_code == 200 else ""
        headers = {"Authorization": f"Bearer {token}"}

        dash = client.get("/api/v1/admin/dashboard", headers=headers)
        dash_detail = (
            f"active={dash.json().get('promocodes_active')}"
            if dash.status_code == 200
            else dash.text
        )
        check("dashboard", dash.status_code == 200, dash_detail)

        defaults = client.get("/api/v1/admin/promocodes/defaults", headers=headers)
        check("defaults", defaults.status_code == 200)
        payload = defaults.json() if defaults.status_code == 200 else {}
        check(
            "defaults has campaign",
            bool(payload.get("default_campaign_id")),
            str(payload.get("campaigns", [])[:1]),
        )
        check("defaults expires", bool(payload.get("expires_at")))

        table = client.get("/api/v1/admin/tables/promocodes?limit=5", headers=headers)
        total = table.json().get("total") if table.status_code == 200 else None
        check("list promocodes", table.status_code == 200 and (total or 0) >= 20, f"total={total}")

        created = client.post(
            "/api/v1/admin/promocodes",
            headers=headers,
            json={
                "customer_erp_id": "99901",
                "promocode": "220099901",
                "campaign_id": payload.get("default_campaign_id"),
                "customer_name": "Smoke Test Card",
                "reason": "local smoke create",
            },
        )
        check("create card", created.status_code == 201, created.text[:300])
        promo_id = created.json().get("entity_id") if created.status_code == 201 else None

        if promo_id:
            detail = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
            check(
                "get detail",
                detail.status_code == 200 and detail.json().get("customer_card") == "220099901",
                detail.text[:200],
            )

            used = client.patch(
                f"/api/v1/admin/promocodes/{promo_id}",
                headers=headers,
                json={"status": "USED", "customer_phone": "+995111", "reason": "smoke mark used"},
            )
            check("mark USED", used.status_code == 200, used.text[:200])

            active = client.patch(
                f"/api/v1/admin/promocodes/{promo_id}",
                headers=headers,
                json={"status": "ACTIVE", "reason": "smoke reactivate"},
            )
            check("reactivate ACTIVE", active.status_code == 200)
            detail2 = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
            check(
                "reactivated redeemed_at cleared",
                detail2.status_code == 200
                and detail2.json().get("status") == "ACTIVE"
                and detail2.json().get("redeemed_at") is None,
            )

            cashier = client.post(
                "/api/v1/cashier/check",
                json={"code": "220099901", "point_id": "local_smoke"},
            )
            cashier_ok = cashier.status_code == 200 and (
                cashier.json().get("status") == "ACTIVE"
                or cashier.json().get("result") == "ACTIVE"
                or "ACTIVE" in str(cashier.json())
            )
            check("cashier sees ACTIVE card", cashier_ok, cashier.text[:300])

            deleted = client.request(
                "DELETE",
                f"/api/v1/admin/promocodes/{promo_id}",
                headers=headers,
                json={"reason": "smoke delete"},
            )
            check("delete card", deleted.status_code == 200, deleted.text[:200])
            gone = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
            check("deleted is 404", gone.status_code == 404)

        first = client.post(
            "/api/v1/admin/promocodes",
            headers=headers,
            json={
                "customer_erp_id": "99902",
                "promocode": "220099902",
                "campaign_id": payload.get("default_campaign_id"),
                "reason": "dup1",
            },
        )
        second = client.post(
            "/api/v1/admin/promocodes",
            headers=headers,
            json={
                "customer_erp_id": "99903",
                "promocode": "220099902",
                "campaign_id": payload.get("default_campaign_id"),
                "reason": "dup2",
            },
        )
        check(
            "duplicate promocode rejected",
            first.status_code == 201 and second.status_code == 400,
            f"{first.status_code}/{second.status_code} {second.text[:120]}",
        )
        if first.status_code == 201:
            client.request(
                "DELETE",
                f"/api/v1/admin/promocodes/{first.json()['entity_id']}",
                headers=headers,
                json={"reason": "cleanup dup"},
            )

        vlogin = client.post(
            "/api/v1/admin/login",
            json={"username": viewer_user, "password": viewer_pass},
        )
        check("viewer login", vlogin.status_code == 200)
        vheaders = {"Authorization": f"Bearer {vlogin.json()['token']}"}
        vcreate = client.post(
            "/api/v1/admin/promocodes",
            headers=vheaders,
            json={"customer_erp_id": "1", "promocode": "12345678", "reason": "viewer blocked"},
        )
        check("viewer cannot create", vcreate.status_code == 403)
        vdefaults = client.get("/api/v1/admin/promocodes/defaults", headers=vheaders)
        check("viewer can read defaults", vdefaults.status_code == 200)

    for path in ["/admin/login", "/admin/dashboard", "/admin/cards", "/admin/cards/new"]:
        response = httpx.get(f"http://127.0.0.1:5173{path}", timeout=10.0)
        check(f"vite {path}", response.status_code == 200, str(response.status_code))

    print("\nSUMMARY:", "ALL PASS" if not errors else f"{len(errors)} FAILED: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
