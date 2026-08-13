from __future__ import annotations

import httpx
import pytest
from app.core.config import Settings
from app.models import TelegramNotificationLog
from app.models.telegram_subscriber import TelegramSubscriber
from app.services.telegram import send_alert
from app.services.telegram_bot import (
    CALLBACK_TOGGLE_PREFIX,
    process_bot_updates,
    topics_inline_keyboard,
)
from app.services.telegram_subscribers import (
    list_recipient_chat_ids,
    subscribe,
    toggle_subscriber_topic,
)
from app.services.telegram_topics import (
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    TOPIC_DIGEST,
    TOPIC_SALES,
    TOPIC_SCANS,
    TOPIC_SYSTEM,
    topics_to_csv,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _settings(**overrides: str) -> Settings:
    data = {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_ALERT_CHAT_ID": "",
        "TELEGRAM_DEDUP_WINDOW_SECONDS": "900",
        "TELEGRAM_SUBSCRIBE_KEYWORD": "promo",
        **overrides,
    }
    return Settings(_env_file=None, **data)


def _client(updates: list | None = None) -> httpx.Client:
    payload = {"ok": True, "result": updates or []}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/getUpdates"):
            return httpx.Response(200, json=payload)
        return httpx.Response(200, json={"ok": True})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_sales_only_gets_sale_not_scan(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "sales1", topics=topics_to_csv([TOPIC_SALES, TOPIC_SYSTEM]))
    subscribe(db_session, "scans1", topics=topics_to_csv([TOPIC_SCANS, TOPIC_SYSTEM]))

    send_alert(
        db_session,
        event_type="sale_observed",
        dedup_key="sale:1",
        message="sale",
        settings=settings,
        http_client=_client(),
        skip_dedup=True,
    )
    sale_chats = {
        row.chat_id
        for row in db_session.scalars(select(TelegramNotificationLog)).all()
        if row.delivery_status == "sent" and row.event_type == "sale_observed"
    }
    assert sale_chats == {"sales1"}

    send_alert(
        db_session,
        event_type="cashier_scan",
        dedup_key="scan:1",
        message="scan",
        settings=settings,
        http_client=_client(),
        skip_dedup=True,
    )
    scan_chats = {
        row.chat_id
        for row in db_session.scalars(select(TelegramNotificationLog)).all()
        if row.delivery_status == "sent" and row.event_type == "cashier_scan"
    }
    assert scan_chats == {"scans1"}


def test_system_reaches_digest_only_subscriber(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "digest1", alert_mode=ALERT_MODE_DIGEST)
    chats = list_recipient_chat_ids(db_session, settings, topic=TOPIC_SYSTEM)
    assert "digest1" in chats
    send_alert(
        db_session,
        event_type="job_crash",
        dedup_key="crash:1",
        message="boom",
        settings=settings,
        http_client=_client(),
        skip_dedup=True,
    )
    sent = {
        row.chat_id
        for row in db_session.scalars(select(TelegramNotificationLog)).all()
        if row.delivery_status == "sent"
    }
    assert "digest1" in sent


def test_seed_chat_gets_all_topics(db_session: Session) -> None:
    settings = _settings(TELEGRAM_ALERT_CHAT_ID="seed1")
    subscribe(db_session, "sales1", topics=topics_to_csv([TOPIC_SALES, TOPIC_SYSTEM]))
    chats = list_recipient_chat_ids(db_session, settings, topic=TOPIC_SCANS)
    assert "seed1" in chats
    assert "sales1" not in chats


def test_full_and_digest_presets_match_legacy(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "full1", alert_mode=ALERT_MODE_FULL)
    subscribe(db_session, "digest1", alert_mode=ALERT_MODE_DIGEST)

    event_chats = set(list_recipient_chat_ids(db_session, settings, topic=TOPIC_SCANS))
    digest_chats = set(list_recipient_chat_ids(db_session, settings, topic=TOPIC_DIGEST))
    assert event_chats == {"full1"}
    assert digest_chats == {"full1", "digest1"}


def test_toggle_topic_updates_db(db_session: Session) -> None:
    subscribe(db_session, "u1", alert_mode=ALERT_MODE_FULL)
    row = db_session.get(TelegramSubscriber, "u1")
    assert row is not None
    assert TOPIC_SCANS in (row.topics or "")
    new_csv = toggle_subscriber_topic(db_session, "u1", TOPIC_SCANS)
    assert new_csv is not None
    assert TOPIC_SCANS not in new_csv
    assert TOPIC_SYSTEM in new_csv
    db_session.refresh(row)
    assert row.alert_mode == "custom"


def test_callback_toggle_via_process_updates(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "42", alert_mode=ALERT_MODE_FULL)
    updates = [
        {
            "update_id": 10,
            "callback_query": {
                "id": "cq1",
                "data": f"{CALLBACK_TOGGLE_PREFIX}{TOPIC_SCANS}",
                "message": {"message_id": 7, "chat": {"id": 42}},
            },
        }
    ]
    handled = process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client(updates),
    )
    assert handled == 1
    row = db_session.get(TelegramSubscriber, "42")
    assert row is not None
    assert TOPIC_SCANS not in row.topics


def test_inline_keyboard_marks_system_locked() -> None:
    markup = topics_inline_keyboard(topics_to_csv([TOPIC_DIGEST, TOPIC_SYSTEM]))
    labels = [btn["text"] for row in markup["inline_keyboard"] for btn in row]
    assert any(t.startswith("🔒") for t in labels)
    assert any("✅" in t and "Сводки" in t for t in labels)
