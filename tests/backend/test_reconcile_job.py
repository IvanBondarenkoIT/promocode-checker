from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import Settings
from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.jobs.reconcile import run_reconcile
from app.models import (
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    Promocode,
    PromocodeStatus,
)
from app.services.promocode_close import close_promocode
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _settings(**overrides: str) -> Settings:
    data = {
        "FRAUD_MATCH_WINDOW_HOURS": "2",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_ALERT_CHAT_ID": "",
        "ERP_ACCESS_MODE": "mock",
        **overrides,
    }
    return Settings(_env_file=None, **data)


def _create_active(
    db: Session,
    *,
    code: str,
    customer: str,
    created_at: datetime,
    expires_at: datetime | None = None,
) -> Promocode:
    promo = Promocode(
        customer_erp_id=customer,
        promocode=code,
        status=PromocodeStatus.ACTIVE,
        created_at=created_at,
        expires_at=expires_at or (created_at + timedelta(days=30)),
    )
    db.add(promo)
    db.flush()
    return promo


def test_reconcile_auto_closes_active_with_sale(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000001",
        customer="CUST-A",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [
            CoffeeSaleMatch(
                customer_erp_id="CUST-A",
                sold_at=now - timedelta(hours=1),
                group_id=11077,
                product_name="beans",
            )
        ]
    )

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=adapter,
        now=now,
    )

    db_session.refresh(promo)
    assert result.auto_closed == ["10000001"]
    assert promo.status == PromocodeStatus.USED
    assert promo.redeemed_at == now

    log = db_session.scalar(
        select(CheckerLog).where(CheckerLog.action_type == CheckerActionType.AUTO_CLOSE)
    )
    assert log is not None
    assert log.erp_sale_matched is True
    assert log.point_id == "reconcile"


def test_reconcile_fraud_when_manual_close_without_sale(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000002",
        customer="CUST-B",
        created_at=now - timedelta(hours=5),
    )
    close_promocode(
        db_session,
        promo,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        erp_sale_matched=False,
        now=now - timedelta(hours=3),
    )

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=MockErpAdapter([]),
        now=now,
    )

    assert result.fraud_warnings == ["10000002"]
    warning = db_session.scalar(select(FraudWarning))
    assert warning is not None
    assert warning.promocode_value == "10000002"
    assert warning.status.value == "OPEN"


def test_reconcile_no_fraud_when_sale_in_window(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000003",
        customer="CUST-C",
        created_at=now - timedelta(hours=5),
    )
    redeemed_at = now - timedelta(hours=3)
    close_promocode(
        db_session,
        promo,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        now=redeemed_at,
    )
    adapter = MockErpAdapter(
        [
            CoffeeSaleMatch(
                customer_erp_id="CUST-C",
                sold_at=redeemed_at + timedelta(minutes=20),
                group_id=16279,
            )
        ]
    )

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=adapter,
        now=now,
    )

    assert result.fraud_warnings == []
    assert db_session.scalar(select(FraudWarning)) is None


def test_reconcile_respects_soft_amnesty_window(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000004",
        customer="CUST-D",
        created_at=now - timedelta(hours=2),
    )
    close_promocode(
        db_session,
        promo,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        now=now - timedelta(hours=1),  # still inside 2h amnesty
    )

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=MockErpAdapter([]),
        now=now,
    )

    assert result.fraud_warnings == []
    assert db_session.scalar(select(FraudWarning)) is None


def test_reconcile_skips_already_warned_manual_close(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000005",
        customer="CUST-E",
        created_at=now - timedelta(hours=6),
    )
    log = close_promocode(
        db_session,
        promo,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        now=now - timedelta(hours=4),
    )
    db_session.add(
        FraudWarning(
            promocode_id=promo.id,
            checker_log_id=log.id,
            point_id=log.point_id,
            customer_erp_id=promo.customer_erp_id,
            promocode_value=promo.promocode,
            message="already open",
            detected_at=now - timedelta(hours=1),
        )
    )
    db_session.flush()

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=MockErpAdapter([]),
        now=now,
    )

    assert result.fraud_warnings == []
    warnings = list(db_session.scalars(select(FraudWarning)).all())
    assert len(warnings) == 1
