from datetime import UTC, datetime, timedelta

import pytest
from app.models import (
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    FraudWarningStatus,
    Promocode,
    PromocodeStatus,
    SaleObservation,
    TelegramNotificationLog,
)
from app.services.promocode_close import close_promocode
from app.services.promocode_status import (
    PromocodeLookupState,
    format_status_card,
    lookup_promocode_status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _promo(
    db: Session,
    *,
    code: str = "220000019999",
    status: PromocodeStatus = PromocodeStatus.ACTIVE,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> Promocode:
    now = created_at or datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    row = Promocode(
        customer_erp_id="CUST-S",
        promocode=code,
        status=status,
        customer_name="Status Client",
        created_at=now,
        expires_at=expires_at or (now + timedelta(days=30)),
    )
    db.add(row)
    db.flush()
    return row


def test_invalid_and_not_found(db_session: Session) -> None:
    bad = lookup_promocode_status(db_session, "abc")
    assert bad.state == PromocodeLookupState.INVALID_FORMAT
    missing = lookup_promocode_status(db_session, "220000010000")
    assert missing.state == PromocodeLookupState.NOT_FOUND


def test_active_and_expired(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 15, 0, tzinfo=UTC)
    _promo(db_session, code="220000010101", created_at=now - timedelta(days=1))
    active = lookup_promocode_status(db_session, "220000010101", now=now)
    assert active.state == PromocodeLookupState.ACTIVE

    _promo(
        db_session,
        code="220000010102",
        created_at=now - timedelta(days=40),
        expires_at=now - timedelta(days=1),
    )
    expired = lookup_promocode_status(db_session, "220000010102", now=now)
    assert expired.state == PromocodeLookupState.EXPIRED


def test_closed_auto(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 15, 0, tzinfo=UTC)
    promo = _promo(db_session, code="220000010103", created_at=now - timedelta(hours=5))
    close_promocode(
        db_session,
        promo,
        action_type=CheckerActionType.AUTO_CLOSE,
        point_id="reconcile",
        erp_sale_matched=True,
        now=now - timedelta(hours=1),
    )
    db_session.add(
        SaleObservation(
            promocode_id=promo.id,
            promocode_value=promo.promocode,
            customer_erp_id=promo.customer_erp_id,
            order_id="ord-auto",
            sold_at=now - timedelta(hours=2),
            order_kg=2.0,
            verdict="QUALIFIED",
            enforcement_mode="enforce",
            promocode_closed=True,
            detected_at=now - timedelta(hours=1),
        )
    )
    db_session.flush()
    card = lookup_promocode_status(db_session, "220000010103", now=now)
    assert card.state == PromocodeLookupState.CLOSED_AUTO
    assert card.order_id == "ord-auto"
    text = format_status_card(card)
    assert "автоматически" in text.lower()


def test_closed_manual_waiting_confirmed_and_fraud(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 15, 0, tzinfo=UTC)
    waiting = _promo(db_session, code="220000010104", created_at=now - timedelta(hours=3))
    close_promocode(
        db_session,
        waiting,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        erp_sale_matched=False,
        now=now - timedelta(hours=1),
    )
    card_w = lookup_promocode_status(db_session, "220000010104", now=now)
    assert card_w.state == PromocodeLookupState.CLOSED_MANUAL_WAITING
    assert card_w.waiting_hours_left is not None
    assert card_w.waiting_hours_left > 0

    confirmed = _promo(db_session, code="220000010105", created_at=now - timedelta(hours=5))
    close_promocode(
        db_session,
        confirmed,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        erp_sale_matched=True,
        now=now - timedelta(hours=3),
    )
    card_c = lookup_promocode_status(db_session, "220000010105", now=now)
    assert card_c.state == PromocodeLookupState.CLOSED_MANUAL_CONFIRMED

    fraud_promo = _promo(db_session, code="220000010106", created_at=now - timedelta(hours=6))
    log = close_promocode(
        db_session,
        fraud_promo,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id="shop_01",
        now=now - timedelta(hours=4),
    )
    db_session.add(
        FraudWarning(
            promocode_id=fraud_promo.id,
            checker_log_id=log.id,
            point_id="shop_01",
            customer_erp_id=fraud_promo.customer_erp_id,
            promocode_value=fraud_promo.promocode,
            status=FraudWarningStatus.OPEN,
            message="no sale",
            detected_at=now - timedelta(hours=1),
        )
    )
    db_session.flush()
    card_f = lookup_promocode_status(db_session, "220000010106", now=now)
    assert card_f.state == PromocodeLookupState.CLOSED_MANUAL_NO_SALE


def test_lookup_is_read_only(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 15, 0, tzinfo=UTC)
    _promo(db_session, code="220000010107", created_at=now)
    before_logs = db_session.scalar(select(func.count()).select_from(CheckerLog)) or 0
    before_tg = db_session.scalar(select(func.count()).select_from(TelegramNotificationLog)) or 0
    lookup_promocode_status(db_session, "220000010107", now=now)
    after_logs = db_session.scalar(select(func.count()).select_from(CheckerLog)) or 0
    after_tg = db_session.scalar(select(func.count()).select_from(TelegramNotificationLog)) or 0
    assert after_logs == before_logs
    assert after_tg == before_tg
