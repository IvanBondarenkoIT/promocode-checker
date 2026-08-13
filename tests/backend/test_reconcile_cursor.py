from datetime import UTC, datetime, timedelta

import pytest
from app.integrations.erp.base import ErpError
from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.jobs.reconcile import run_reconcile
from app.models import ReconcileState, SaleObservation, TelegramNotificationLog
from app.services.reconcile_state import (
    compute_observe_window,
    local_date,
    start_of_local_day,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available
from tests.backend.test_reconcile_job import _create_active, _qualified_sale, _settings

TZ = "Asia/Tbilisi"


def test_compute_window_first_run_uses_floor_start_of_day() -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    window = compute_observe_window(
        now=now,
        earliest_created=created,
        last_scan_until=None,
        overlap_hours=48,
        tz_name=TZ,
    )
    assert window.used_cursor is False
    assert window.until == now
    assert window.since == start_of_local_day(created, TZ)
    assert window.since < created


def test_compute_window_steady_uses_cursor_minus_overlap_not_oldest() -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = datetime(2026, 7, 15, 8, 0, tzinfo=UTC)
    cursor = now - timedelta(minutes=10)
    window = compute_observe_window(
        now=now,
        earliest_created=created,
        last_scan_until=cursor,
        overlap_hours=48,
        tz_name=TZ,
    )
    assert window.used_cursor is True
    expected = start_of_local_day(cursor - timedelta(hours=48), TZ)
    assert window.since == expected
    assert window.since > start_of_local_day(created, TZ)


def test_compute_window_downtime_expands_back() -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
    stale_cursor = now - timedelta(days=5)
    window = compute_observe_window(
        now=now,
        earliest_created=created,
        last_scan_until=stale_cursor,
        overlap_hours=48,
        tz_name=TZ,
    )
    expected = start_of_local_day(stale_cursor - timedelta(hours=48), TZ)
    assert window.since == expected
    assert now - window.since > timedelta(days=5)


def test_local_date_same_calendar_day_in_tbilisi() -> None:
    created = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    sold_midnight = datetime(2026, 8, 13, 0, 0, tzinfo=UTC)
    assert local_date(sold_midnight, TZ) == local_date(created, TZ)
    previous = datetime(2026, 8, 12, 0, 0, tzinfo=UTC)
    assert local_date(previous, TZ) < local_date(created, TZ)


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_first_reconcile_window_uses_oldest_code_day(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = now - timedelta(days=10)
    _create_active(db_session, code="220000010001", customer="CUST-W", created_at=created)
    adapter = MockErpAdapter([])
    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=adapter,
        now=now,
    )
    assert result.window_since == start_of_local_day(created, TZ)
    assert result.window_until == now
    assert adapter.last_since == result.window_since
    state = db_session.get(ReconcileState, 1)
    assert state is not None
    assert state.last_scan_until == now


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_second_reconcile_window_does_not_grow_tail(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = now - timedelta(days=10)
    _create_active(db_session, code="220000010002", customer="CUST-W2", created_at=created)
    adapter = MockErpAdapter([])
    settings = _settings()
    first = run_reconcile(db_session, settings=settings, adapter=adapter, now=now)
    later = now + timedelta(minutes=10)
    second = run_reconcile(db_session, settings=settings, adapter=adapter, now=later)

    assert first.window_since == start_of_local_day(created, TZ)
    expected = start_of_local_day(now - timedelta(hours=48), TZ)
    assert second.window_since == expected
    assert second.window_since > first.window_since
    assert later - second.window_since <= timedelta(hours=72)


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_stale_cursor_expands_window_after_downtime(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    created = now - timedelta(days=20)
    _create_active(db_session, code="220000010003", customer="CUST-W3", created_at=created)
    settings = _settings()
    first_now = now - timedelta(days=5)
    adapter = MockErpAdapter([])
    run_reconcile(db_session, settings=settings, adapter=adapter, now=first_now)
    result = run_reconcile(db_session, settings=settings, adapter=adapter, now=now)
    expected = start_of_local_day(first_now - timedelta(hours=48), TZ)
    assert result.window_since == expected
    assert now - result.window_since > timedelta(days=5)
    assert result.window_since > start_of_local_day(created, TZ)


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_erp_error_does_not_move_cursor(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    _create_active(
        db_session,
        code="220000010004",
        customer="CUST-W4",
        created_at=now - timedelta(days=2),
    )
    settings = _settings()
    run_reconcile(db_session, settings=settings, adapter=MockErpAdapter([]), now=now)
    state = db_session.get(ReconcileState, 1)
    assert state is not None
    frozen = state.last_scan_until

    class BoomAdapter:
        def find_coffee_sales(self, *args: object, **kwargs: object) -> list[CoffeeSaleMatch]:
            raise ErpError("firebird down")

    with pytest.raises(ErpError, match="firebird down"):
        run_reconcile(
            db_session,
            settings=settings,
            adapter=BoomAdapter(),  # type: ignore[arg-type]
            now=now + timedelta(minutes=10),
        )
    db_session.refresh(state)
    assert state.last_scan_until == frozen


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_sale_on_code_issue_day_is_observed(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    _create_active(db_session, code="220000010005", customer="CUST-W5", created_at=now)
    sold_at = datetime(2026, 8, 13, 0, 0, tzinfo=UTC)
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-W5", sold_at, order_id="ord-sameday", qty=0.25)]
    )
    result = run_reconcile(
        db_session,
        settings=_settings(PROMO_ENFORCEMENT_MODE="monitor"),
        adapter=adapter,
        now=now,
    )
    assert result.observed == ["ord-sameday"]
    obs = db_session.scalar(select(SaleObservation))
    assert obs is not None
    assert obs.order_id == "ord-sameday"


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_sale_before_code_issue_day_is_skipped(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    _create_active(db_session, code="220000010006", customer="CUST-W6", created_at=now)
    sold_at = datetime(2026, 8, 12, 0, 0, tzinfo=UTC)
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-W6", sold_at, order_id="ord-prevday", qty=2.0)]
    )
    result = run_reconcile(
        db_session,
        settings=_settings(PROMO_ENFORCEMENT_MODE="monitor"),
        adapter=adapter,
        now=now,
    )
    assert result.observed == []
    assert db_session.scalar(select(SaleObservation)) is None


@pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)
def test_repeat_run_does_not_duplicate_observation_or_alert(db_session: Session) -> None:
    now = datetime(2026, 8, 13, 13, 47, tzinfo=UTC)
    _create_active(
        db_session,
        code="220000010007",
        customer="CUST-W7",
        created_at=now - timedelta(hours=3),
    )
    adapter = MockErpAdapter(
        [_qualified_sale("CUST-W7", now - timedelta(hours=1), order_id="ord-once")]
    )
    settings = _settings(PROMO_ENFORCEMENT_MODE="monitor")
    first = run_reconcile(db_session, settings=settings, adapter=adapter, now=now)
    second = run_reconcile(
        db_session,
        settings=settings,
        adapter=adapter,
        now=now + timedelta(minutes=10),
    )
    assert first.observed == ["ord-once"]
    assert second.observed == []
    count = db_session.scalar(select(func.count()).select_from(SaleObservation))
    assert count == 1
    alerts = list(
        db_session.scalars(
            select(TelegramNotificationLog).where(
                TelegramNotificationLog.event_type == "sale_observed"
            )
        ).all()
    )
    assert len(alerts) == 1
