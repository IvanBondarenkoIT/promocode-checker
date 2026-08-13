import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models import (
    AdminAuditLog,
    Campaign,
    CampaignKind,
    CampaignStatus,
    Promocode,
    PromocodeStatus,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _admin_token(client: TestClient, test_settings) -> str:
    login = client.post(
        "/api/v1/admin/login",
        json={"username": test_settings.admin_username, "password": test_settings.admin_password},
    )
    assert login.status_code == 200
    return login.json()["token"]


def _viewer_token(client: TestClient, test_settings) -> str:
    login = client.post(
        "/api/v1/admin/login",
        json={"username": test_settings.viewer_username, "password": test_settings.viewer_password},
    )
    assert login.status_code == 200
    return login.json()["token"]


def _create_promocode(db_session: Session, *, code: str = "88888888") -> Promocode:
    promo = Promocode(
        customer_erp_id="CUST-ADMIN",
        promocode=code,
        status=PromocodeStatus.USED,
        expires_at=datetime.now(UTC) + timedelta(days=5),
        redeemed_at=datetime.now(UTC),
    )
    db_session.add(promo)
    db_session.flush()
    return promo


def _create_campaign(db_session: Session, *, code: str = "ADMIN_TEST") -> Campaign:
    campaign = Campaign(
        code=code,
        name="Admin test campaign",
        status=CampaignStatus.ACTIVE,
        kind=CampaignKind.TEST,
    )
    db_session.add(campaign)
    db_session.flush()
    return campaign


def test_admin_login_and_viewer_cannot_patch(client: TestClient, test_settings) -> None:
    token = _viewer_token(client, test_settings)

    me = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "viewer"

    patch = client.patch(
        f"/api/v1/admin/promocodes/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ACTIVE", "reason": "should fail"},
    )
    assert patch.status_code == 403


def test_admin_patch_promocode_writes_audit(
    client: TestClient,
    db_session: Session,
    test_settings,
) -> None:
    promo = _create_promocode(db_session, code="77777777")
    token = _admin_token(client, test_settings)

    response = client.patch(
        f"/api/v1/admin/promocodes/{promo.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ACTIVE", "reason": "customer returned unused code"},
    )
    assert response.status_code == 200
    assert response.json()["audit_log_id"] is not None

    db_session.refresh(promo)
    assert promo.status == PromocodeStatus.ACTIVE
    assert promo.redeemed_at is None

    audit = db_session.scalar(select(AdminAuditLog).where(AdminAuditLog.entity_id == str(promo.id)))
    assert audit is not None
    assert audit.reason == "customer returned unused code"
    assert audit.old_values["status"] == "USED"
    assert audit.new_values["status"] == "ACTIVE"


def test_admin_create_get_patch_delete_promocode(
    client: TestClient,
    db_session: Session,
    test_settings,
) -> None:
    campaign = _create_campaign(db_session, code="CARD_FORM_TEST")
    token = _admin_token(client, test_settings)
    headers = {"Authorization": f"Bearer {token}"}

    defaults = client.get("/api/v1/admin/promocodes/defaults", headers=headers)
    assert defaults.status_code == 200
    assert defaults.json()["status"] == "ACTIVE"
    assert defaults.json()["expires_at"]
    assert any(row["code"] == "CARD_FORM_TEST" for row in defaults.json()["campaigns"])

    created = client.post(
        "/api/v1/admin/promocodes",
        headers=headers,
        json={
            "customer_erp_id": "21470",
            "promocode": "220021470",
            "campaign_id": str(campaign.id),
            "customer_name": "Shop Batumi",
            "reason": "manual calibration card",
        },
    )
    assert created.status_code == 201
    promo_id = created.json()["entity_id"]

    detail = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["promocode"] == "220021470"
    assert body["customer_card"] == "220021470"
    assert body["campaign_code"] == "CARD_FORM_TEST"
    assert body["status"] == "ACTIVE"

    patched = client.patch(
        f"/api/v1/admin/promocodes/{promo_id}",
        headers=headers,
        json={
            "status": "USED",
            "customer_phone": "+995555",
            "reason": "mark used for test",
        },
    )
    assert patched.status_code == 200

    detail2 = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
    assert detail2.json()["status"] == "USED"
    assert detail2.json()["customer_phone"] == "+995555"

    reactivated = client.patch(
        f"/api/v1/admin/promocodes/{promo_id}",
        headers=headers,
        json={"status": "ACTIVE", "reason": "reactivate for cashier"},
    )
    assert reactivated.status_code == 200
    detail_active = client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers)
    assert detail_active.json()["status"] == "ACTIVE"

    deleted = client.request(
        "DELETE",
        f"/api/v1/admin/promocodes/{promo_id}",
        headers=headers,
        json={"reason": "remove test card"},
    )
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/admin/promocodes/{promo_id}", headers=headers).status_code == 404

    audits = db_session.scalars(
        select(AdminAuditLog).where(AdminAuditLog.entity_id == promo_id).order_by(AdminAuditLog.id)
    ).all()
    actions = [row.action for row in audits]
    assert "admin_create" in actions
    assert "admin_delete" in actions


def test_viewer_cannot_create_or_delete(client: TestClient, test_settings) -> None:
    token = _viewer_token(client, test_settings)
    headers = {"Authorization": f"Bearer {token}"}
    create = client.post(
        "/api/v1/admin/promocodes",
        headers=headers,
        json={
            "customer_erp_id": "1",
            "promocode": "12345678",
            "reason": "viewer blocked",
        },
    )
    assert create.status_code == 403
    delete = client.request(
        "DELETE",
        f"/api/v1/admin/promocodes/{uuid.uuid4()}",
        headers=headers,
        json={"reason": "viewer blocked"},
    )
    assert delete.status_code == 403


def test_admin_dashboard_and_tables(client: TestClient, test_settings) -> None:
    token = _admin_token(client, test_settings)
    headers = {"Authorization": f"Bearer {token}"}

    dashboard = client.get("/api/v1/admin/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert "promocodes_active" in dashboard.json()

    table = client.get("/api/v1/admin/tables/promocodes", headers=headers)
    assert table.status_code == 200
    assert table.json()["table"] == "promocodes"
