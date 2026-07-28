"""Tests for concurrent/sequential redeem row locking."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

import pytest
from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus
from app.schemas.cashier import CashierResult
from app.services.cashier import redeem_promocode
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _create_active(engine, *, code: str) -> None:
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        session.add(
            Promocode(
                customer_erp_id="CUST-LOCK",
                promocode=code,
                status=PromocodeStatus.ACTIVE,
                expires_at=datetime.now(UTC) + timedelta(days=10),
            )
        )
        session.commit()
    finally:
        session.close()


def _redeem_in_thread(engine, code: str, results: list, index: int) -> None:
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        response = redeem_promocode(session, code=code, point_id="shop_lock")
        session.commit()
        results[index] = response
    except Exception as exc:  # noqa: BLE001 — capture thread failures
        session.rollback()
        results[index] = exc
    finally:
        session.close()


def test_sequential_double_redeem_writes_one_manual_close(engine) -> None:
    code = "44444444"
    _create_active(engine, code=code)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    try:
        first = redeem_promocode(session, code=code, point_id="shop_01")
        session.commit()
        second = redeem_promocode(session, code=code, point_id="shop_01")
        session.commit()

        assert first.result == CashierResult.REDEEMED
        assert second.result == CashierResult.USED
        assert second.log_id is None

        close_count = session.scalar(
            select(func.count())
            .select_from(CheckerLog)
            .where(
                CheckerLog.scanned_code == code,
                CheckerLog.action_type == CheckerActionType.MANUAL_CLOSE,
            )
        )
        assert close_count == 1
    finally:
        session.close()


def test_concurrent_redeem_only_one_manual_close(engine) -> None:
    code = "55555555"
    _create_active(engine, code=code)

    results: list = [None, None]
    threads = [
        threading.Thread(target=_redeem_in_thread, args=(engine, code, results, 0)),
        threading.Thread(target=_redeem_in_thread, args=(engine, code, results, 1)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not isinstance(item, Exception) for item in results)

    outcomes = {item.result for item in results}
    assert CashierResult.REDEEMED in outcomes
    assert CashierResult.USED in outcomes

    verify = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        close_count = verify.scalar(
            select(func.count())
            .select_from(CheckerLog)
            .where(
                CheckerLog.scanned_code == code,
                CheckerLog.action_type == CheckerActionType.MANUAL_CLOSE,
            )
        )
        promo = verify.scalar(select(Promocode).where(Promocode.promocode == code))
        assert close_count == 1
        assert promo is not None
        assert promo.status == PromocodeStatus.USED
    finally:
        verify.close()
