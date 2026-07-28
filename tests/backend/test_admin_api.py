import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models import AdminAuditLog, Promocode, PromocodeStatus
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


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


def test_admin_login_and_viewer_cannot_patch(client: TestClient, test_settings) -> None:
    login = client.post(
        "/api/v1/admin/login",
        json={"username": test_settings.viewer_username, "password": test_settings.viewer_password},
    )
    assert login.status_code == 200
    token = login.json()["token"]

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
    login = client.post(
        "/api/v1/admin/login",
        json={"username": test_settings.admin_username, "password": test_settings.admin_password},
    )
    token = login.json()["token"]

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


def test_admin_dashboard_and_tables(client: TestClient, test_settings) -> None:
    login = client.post(
        "/api/v1/admin/login",
        json={"username": test_settings.admin_username, "password": test_settings.admin_password},
    )
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    dashboard = client.get("/api/v1/admin/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert "promocodes_active" in dashboard.json()

    table = client.get("/api/v1/admin/tables/promocodes", headers=headers)
    assert table.status_code == 200
    assert table.json()["table"] == "promocodes"
