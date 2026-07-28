from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import Settings
from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _create_promocode(
    db_session: Session,
    *,
    code: str,
    status: PromocodeStatus = PromocodeStatus.ACTIVE,
    expires_at: datetime | None = None,
    redeemed_at: datetime | None = None,
) -> Promocode:
    promocode = Promocode(
        customer_erp_id="CUST-TEST",
        promocode=code,
        status=status,
        expires_at=expires_at or (datetime.now(UTC) + timedelta(days=10)),
        redeemed_at=redeemed_at,
    )
    db_session.add(promocode)
    db_session.flush()
    return promocode


def test_check_valid_promocode_creates_scan_log(
    client: TestClient,
    db_session: Session,
    test_settings: Settings,
) -> None:
    promocode = _create_promocode(db_session, code="12345678")

    response = client.post("/api/v1/cashier/check", json={"code": promocode.promocode})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "valid"
    assert payload["status"] == "ACTIVE"
    assert payload["point_id"] == test_settings.default_point_id
    assert payload["log_id"] is not None

    log = db_session.get(CheckerLog, payload["log_id"])
    assert log is not None
    assert log.action_type == CheckerActionType.SCAN_CHECK
    assert log.promocode_id == promocode.id
    assert log.scanned_code == "12345678"


def test_check_invalid_format_skips_log(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/cashier/check", json={"code": "abc"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "invalid_format"
    assert payload["log_id"] is None
    assert db_session.scalar(select(CheckerLog.id)) is None


def test_check_not_found_still_logs(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/cashier/check",
        json={"code": "87654321", "point_id": "shop_99"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "not_found"
    assert payload["point_id"] == "shop_99"
    log = db_session.get(CheckerLog, payload["log_id"])
    assert log is not None
    assert log.promocode_id is None
    assert log.action_type == CheckerActionType.SCAN_CHECK


def test_check_expired_and_used(client: TestClient, db_session: Session) -> None:
    expired = _create_promocode(
        db_session,
        code="11111111",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    used = _create_promocode(
        db_session,
        code="22222222",
        status=PromocodeStatus.USED,
        redeemed_at=datetime.now(UTC),
    )

    expired_response = client.post("/api/v1/cashier/check", json={"code": expired.promocode})
    used_response = client.post("/api/v1/cashier/check", json={"code": used.promocode})

    assert expired_response.json()["result"] == "expired"
    assert used_response.json()["result"] == "used"


def test_redeem_success_and_repeat_is_used(client: TestClient, db_session: Session) -> None:
    promocode = _create_promocode(db_session, code="33333333")

    first = client.post("/api/v1/cashier/redeem", json={"code": promocode.promocode})
    second = client.post("/api/v1/cashier/redeem", json={"code": promocode.promocode})

    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["result"] == "redeemed"
    assert first_payload["status"] == "USED"
    assert first_payload["redeemed_at"] is not None

    log = db_session.get(CheckerLog, first_payload["log_id"])
    assert log is not None
    assert log.action_type == CheckerActionType.MANUAL_CLOSE

    db_session.refresh(promocode)
    assert promocode.status == PromocodeStatus.USED

    assert second.status_code == 200
    assert second.json()["result"] == "used"
    assert second.json()["log_id"] is None


def test_barcode_returns_png(client: TestClient) -> None:
    response = client.get("/api/v1/cashier/barcode/12345678")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_barcode_rejects_invalid_code(client: TestClient) -> None:
    response = client.get("/api/v1/cashier/barcode/12ab")

    assert response.status_code == 422
