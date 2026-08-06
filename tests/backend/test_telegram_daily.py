"""Tests for Telegram alert audiences and daily digests."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import httpx
import pytest
from app.core.config import Settings
from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.jobs.telegram_daily import run_telegram_daily
from app.models import TelegramNotificationLog
from app.models.enums import CheckerActionType
from app.models.telegram_subscriber import (
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    TelegramDigestState,
    TelegramSubscriber,
)
from app.services.telegram import send_alert
from app.services.telegram_bot import process_bot_updates
from app.services.telegram_messages import msg_day_end, msg_day_start, msg_digest_error
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _settings(**overrides: object) -> Settings:
    data = {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_ALERT_CHAT_ID": "",
        "TELEGRAM_DEDUP_WINDOW_SECONDS": "900",
        "APP_TIMEZONE": "Asia/Tbilisi",
        "TELEGRAM_DAY_START_HOUR": "10",
        "TELEGRAM_DAY_START_MINUTE": "0",
        "TELEGRAM_EOD_HOUR": "22",
        "TELEGRAM_EOD_MINUTE": "0",
        **overrides,
    }
    return Settings(
        _env_file=None,
        **{k: str(v) if not isinstance(v, str) else v for k, v in data.items()},
    )


def _client() -> httpx.Client:
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"ok": True}))
    return httpx.Client(transport=transport)


def test_send_alert_events_skips_digest_subscribers(db_session: Session) -> None:
    settings = _settings()
    db_session.add(
        TelegramSubscriber(chat_id="full1", active=True, alert_mode=ALERT_MODE_FULL)
    )
    db_session.add(
        TelegramSubscriber(chat_id="digest1", active=True, alert_mode=ALERT_MODE_DIGEST)
    )
    db_session.flush()

    send_alert(
        db_session,
        event_type="cashier_scan",
        dedup_key="scan:test:1",
        message="scan",
        settings=settings,
        http_client=_client(),
        audience="events",
        skip_dedup=True,
    )
    chats = {
        row.chat_id
        for row in db_session.scalars(select(TelegramNotificationLog)).all()
        if row.delivery_status == "sent"
    }
    assert chats == {"full1"}


def test_send_alert_digest_reaches_both_modes(db_session: Session) -> None:
    settings = _settings()
    db_session.add(
        TelegramSubscriber(chat_id="full1", active=True, alert_mode=ALERT_MODE_FULL)
    )
    db_session.add(
        TelegramSubscriber(chat_id="digest1", active=True, alert_mode=ALERT_MODE_DIGEST)
    )
    db_session.flush()

    send_alert(
        db_session,
        event_type="day_start",
        dedup_key="day_start:test",
        message="day",
        settings=settings,
        http_client=_client(),
        audience="digest",
        skip_dedup=True,
    )
    chats = {
        row.chat_id
        for row in db_session.scalars(select(TelegramNotificationLog)).all()
        if row.delivery_status == "sent"
    }
    assert chats == {"full1", "digest1"}


def test_day_start_idempotent(db_session: Session) -> None:
    settings = _settings()
    db_session.add(
        TelegramSubscriber(chat_id="ops1", active=True, alert_mode=ALERT_MODE_FULL)
    )
    db_session.flush()

    tz = ZoneInfo("Asia/Tbilisi")
    local = datetime(2026, 8, 4, 10, 5, tzinfo=tz)
    adapter = MockErpAdapter(
        sales=[
            CoffeeSaleMatch(
                customer_erp_id="1",
                sold_at=datetime(2026, 8, 4, 9, 0, tzinfo=tz),
                group_id=11077,
                product_name="Coffee A",
                unit_price=45.0,
            )
        ]
    )

    first = run_telegram_daily(
        db_session,
        settings=settings,
        adapter=adapter,
        now=local.astimezone(UTC),
        http_client=_client(),
    )
    second = run_telegram_daily(
        db_session,
        settings=settings,
        adapter=adapter,
        now=local.astimezone(UTC),
        http_client=_client(),
    )

    assert first.day_start_sent is True
    assert second.day_start_sent is False
    state = db_session.get(TelegramDigestState, 1)
    assert state is not None
    assert state.last_day_start_on.isoformat() == "2026-08-04"
    sent = [
        r
        for r in db_session.scalars(select(TelegramNotificationLog)).all()
        if r.event_type == "day_start" and r.delivery_status == "sent"
    ]
    assert len(sent) == 1


def test_eod_includes_checker_counts(db_session: Session) -> None:
    from app.models import CheckerLog

    settings = _settings()
    db_session.add(
        TelegramSubscriber(chat_id="ops1", active=True, alert_mode=ALERT_MODE_DIGEST)
    )
    tz = ZoneInfo("Asia/Tbilisi")
    scan_at = datetime(2026, 8, 4, 12, 0, tzinfo=tz)
    db_session.add(
        CheckerLog(
            scanned_code="41000001",
            scan_time=scan_at,
            action_type=CheckerActionType.SCAN_CHECK,
            point_id="IVAN",
            erp_sale_matched=False,
        )
    )
    db_session.add(
        CheckerLog(
            scanned_code="41000001",
            scan_time=scan_at,
            action_type=CheckerActionType.AUTO_CLOSE,
            point_id="reconcile",
            erp_sale_matched=True,
        )
    )
    # Pretend day-start already sent so only EOD fires
    db_session.add(
        TelegramDigestState(id=1, last_day_start_on=scan_at.date(), last_eod_on=None)
    )
    db_session.flush()

    local = datetime(2026, 8, 4, 22, 5, tzinfo=tz)
    result = run_telegram_daily(
        db_session,
        settings=settings,
        adapter=MockErpAdapter(sales=[]),
        now=local.astimezone(UTC),
        http_client=_client(),
    )
    assert result.eod_sent is True
    body = next(
        r.message
        for r in db_session.scalars(select(TelegramNotificationLog)).all()
        if r.event_type == "day_end"
    )
    assert "сканы: 1" in body
    assert "автозакрытия: 1" in body


def test_digest_error_on_erp_failure(db_session: Session) -> None:
    class BoomAdapter:
        def find_coffee_sales(self, *args, **kwargs):
            raise RuntimeError("erp down")

    settings = _settings()
    db_session.add(
        TelegramSubscriber(chat_id="ops1", active=True, alert_mode=ALERT_MODE_FULL)
    )
    db_session.flush()

    tz = ZoneInfo("Asia/Tbilisi")
    local = datetime(2026, 8, 4, 10, 5, tzinfo=tz)
    result = run_telegram_daily(
        db_session,
        settings=settings,
        adapter=BoomAdapter(),  # type: ignore[arg-type]
        now=local.astimezone(UTC),
        http_client=_client(),
    )
    assert result.day_start_sent is False
    assert result.errors
    state = db_session.get(TelegramDigestState, 1)
    assert state is None or state.last_day_start_on is None
    assert any(
        r.event_type == "digest_error" and r.delivery_status == "sent"
        for r in db_session.scalars(select(TelegramNotificationLog)).all()
    )


def test_bot_sets_digest_mode(db_session: Session) -> None:
    settings = _settings(TELEGRAM_SUBSCRIBE_KEYWORD="promo")
    payload = {
        "ok": True,
        "result": [
            {
                "update_id": 10,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 777},
                    "text": "promo",
                },
            },
            {
                "update_id": 11,
                "message": {
                    "message_id": 2,
                    "chat": {"id": 777},
                    "text": "/digest",
                },
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("getUpdates"):
            return httpx.Response(200, json=payload)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    handled = process_bot_updates(db_session, settings=settings, http_client=client)
    assert handled == 2
    row = db_session.get(TelegramSubscriber, "777")
    assert row is not None
    assert row.active is True
    assert row.alert_mode == ALERT_MODE_DIGEST


def test_digest_templates_smoke() -> None:
    start = msg_day_start(
        local_date="04.08.2026",
        sales_count=0,
        sales_sum=None,
        top_products=[],
    )
    assert "Рабочий день началась" not in start  # typo guard
    assert "Рабочий день начался" in start
    end = msg_day_end(
        local_date="04.08.2026",
        sales_count=1,
        sales_sum=10.0,
        top_products=[("A", 1)],
        scan_count=2,
        manual_close_count=1,
        auto_close_count=1,
        fraud_count=0,
    )
    assert "Итог дня" in end
    err = msg_digest_error(kind="day_start", detail="boom", local_date="04.08.2026")
    assert "Ошибка дневной сводки" in err
