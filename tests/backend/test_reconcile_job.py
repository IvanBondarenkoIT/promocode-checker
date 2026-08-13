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
    SaleObservation,
)
from app.services.promocode_close import close_promocode
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _settings(**overrides: object) -> Settings:
    data = {
        "FRAUD_MATCH_WINDOW_HOURS": "2",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_ALERT_CHAT_ID": "",
        "ERP_ACCESS_MODE": "mock",
        "PROMO_ENFORCEMENT_MODE": "enforce",
        "PROMO_MIN_COFFEE_KG": "2.0",
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


def _qualified_sale(
    customer: str,
    sold_at: datetime,
    *,
    order_id: str = "ord-1",
    qty: float = 2.0,
    group_id: int = 11077,
    product_name: str = "Coffee blend (250 g)",
) -> CoffeeSaleMatch:
    nw = 0.25 if group_id != 16279 else 1.0
    return CoffeeSaleMatch(
        customer_erp_id=customer,
        sold_at=sold_at,
        group_id=group_id,
        product_name=product_name,
        order_id=order_id,
        unit_price=45.0,
        quantity=qty,
        net_weight_kg=nw,
        line_kg=qty,
    )


def test_reconcile_auto_close_one_telegram_summary(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    _create_active(
        db_session, code="10000011", customer="CUST-A", created_at=now - timedelta(hours=3)
    )
    _create_active(
        db_session, code="10000012", customer="CUST-B", created_at=now - timedelta(hours=3)
    )
    adapter = MockErpAdapter(
        [
            _qualified_sale("CUST-A", now - timedelta(hours=1), order_id="a1"),
            _qualified_sale("CUST-B", now - timedelta(hours=1), order_id="b1"),
        ]
    )
    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=adapter,
        now=now,
    )
    assert sorted(result.auto_closed) == ["10000011", "10000012"]

    from app.models import TelegramNotificationLog

    tg_logs = list(
        db_session.scalars(
            select(TelegramNotificationLog).where(
                TelegramNotificationLog.event_type == "reconcile_auto_close"
            )
        ).all()
    )
    assert len(tg_logs) == 2
    assert all("Продажа кофе" in row.message for row in tg_logs)


def test_reconcile_auto_closes_active_with_sale(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000001",
        customer="CUST-A",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-A", now - timedelta(hours=1), order_id="ord-close")]
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

    obs = db_session.scalar(select(SaleObservation))
    assert obs is not None
    assert obs.verdict == "QUALIFIED"
    assert obs.promocode_closed is True


def test_reconcile_monitor_does_not_close(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000021",
        customer="CUST-M",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-M", now - timedelta(hours=1), order_id="ord-mon")]
    )

    result = run_reconcile(
        db_session,
        settings=_settings(PROMO_ENFORCEMENT_MODE="monitor"),
        adapter=adapter,
        now=now,
    )

    db_session.refresh(promo)
    assert result.auto_closed == []
    assert result.qualified_not_closed == ["10000021"]
    assert promo.status == PromocodeStatus.ACTIVE

    obs = db_session.scalar(select(SaleObservation))
    assert obs is not None
    assert obs.promocode_closed is False
    assert obs.order_kg == pytest.approx(2.0)

    from app.models import TelegramNotificationLog

    tg = db_session.scalar(
        select(TelegramNotificationLog).where(TelegramNotificationLog.event_type == "sale_observed")
    )
    assert tg is not None
    assert "НЕ закрыт" in tg.message
    assert "условие выполнено" in tg.message.lower() or "Акция сработала" in tg.message


def test_reconcile_not_enough_kg_still_observed(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    promo = _create_active(
        db_session,
        code="10000022",
        customer="CUST-N",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [
            _qualified_sale(
                "CUST-N",
                now - timedelta(hours=1),
                order_id="ord-small",
                qty=0.5,
            )
        ]
    )

    result = run_reconcile(
        db_session,
        settings=_settings(PROMO_ENFORCEMENT_MODE="monitor"),
        adapter=adapter,
        now=now,
    )

    db_session.refresh(promo)
    assert result.auto_closed == []
    assert promo.status == PromocodeStatus.ACTIVE
    obs = db_session.scalar(select(SaleObservation))
    assert obs is not None
    assert obs.verdict == "NOT_ENOUGH_KG"
    assert obs.order_kg == pytest.approx(0.5)


def test_reconcile_dedupes_same_order(db_session: Session) -> None:
    now = datetime(2026, 7, 28, 15, 0, tzinfo=UTC)
    _create_active(
        db_session,
        code="10000023",
        customer="CUST-D",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-D", now - timedelta(hours=1), order_id="ord-dup")]
    )
    settings = _settings(PROMO_ENFORCEMENT_MODE="monitor")

    first = run_reconcile(db_session, settings=settings, adapter=adapter, now=now)
    second = run_reconcile(
        db_session,
        settings=settings,
        adapter=adapter,
        now=now + timedelta(minutes=5),
    )

    assert len(first.observed) == 1
    assert second.observed == []
    rows = list(db_session.scalars(select(SaleObservation)).all())
    assert len(rows) == 1


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
        now=now - timedelta(hours=1),
    )

    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=MockErpAdapter([]),
        now=now,
    )

    assert result.fraud_warnings == []


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
