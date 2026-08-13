from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from app.core.config import Settings
from app.models import CheckerLog, Promocode, PromocodeStatus, TelegramNotificationLog
from app.models.telegram_subscriber import TelegramSubscriber
from app.services.telegram_bot import main_reply_keyboard, process_bot_updates
from app.services.telegram_subscribers import subscribe
from app.services.telegram_topics import ALERT_MODE_DIGEST, ALERT_MODE_FULL
from sqlalchemy import func, select
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
        "TELEGRAM_SUBSCRIBE_KEYWORD": "promo",
        "APP_TIMEZONE": "Asia/Tbilisi",
        "FRAUD_MATCH_WINDOW_HOURS": "2",
        **overrides,
    }
    return Settings(_env_file=None, **data)


def _client_capturing(updates: list, sent: list[str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/getUpdates"):
            return httpx.Response(200, json={"ok": True, "result": updates})
        if request.url.path.endswith("/sendMessage"):
            sent.append(request.content.decode("utf-8"))
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(200, json={"ok": True})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_start_includes_persistent_keyboard() -> None:
    kb = main_reply_keyboard()
    assert kb["is_persistent"] is True
    flat = [btn["text"] for row in kb["keyboard"] for btn in row]
    assert "Мои подписки" in flat
    assert "Проверить код" in flat
    assert "Подписчики" in flat


def test_code_from_subscriber_returns_status(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "99", alert_mode=ALERT_MODE_FULL)
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    db_session.add(
        Promocode(
            customer_erp_id="C1",
            promocode="220000018888",
            status=PromocodeStatus.ACTIVE,
            created_at=now,
            expires_at=now + timedelta(days=10),
        )
    )
    db_session.flush()
    sent: list[str] = []
    updates = [
        {
            "update_id": 1,
            "message": {"chat": {"id": 99}, "text": "220000018888"},
        }
    ]
    before_logs = db_session.scalar(select(func.count()).select_from(CheckerLog)) or 0
    before_tg = db_session.scalar(select(func.count()).select_from(TelegramNotificationLog)) or 0
    handled = process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client_capturing(updates, sent),
    )
    assert handled == 1
    assert sent
    body = sent[0]
    assert "Промокод активен" in body or "активен" in body.lower()
    after_logs = db_session.scalar(select(func.count()).select_from(CheckerLog)) or 0
    after_tg = db_session.scalar(select(func.count()).select_from(TelegramNotificationLog)) or 0
    assert after_logs == before_logs
    assert after_tg == before_tg


def test_code_from_stranger_needs_subscribe(db_session: Session) -> None:
    settings = _settings()
    sent: list[str] = []
    updates = [
        {
            "update_id": 2,
            "message": {"chat": {"id": 77}, "text": "220000018887"},
        }
    ]
    handled = process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client_capturing(updates, sent),
    )
    assert handled == 1
    assert sent
    assert "подпишитесь" in sent[0].lower()


def test_new_subscribe_alerts_others_not_self(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "10", alert_mode=ALERT_MODE_FULL)
    db_session.flush()
    sent: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/getUpdates"):
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": [
                        {
                            "update_id": 10,
                            "message": {
                                "chat": {"id": 20},
                                "from": {
                                    "id": 20,
                                    "username": "newbie",
                                    "first_name": "New",
                                    "last_name": "User",
                                },
                                "text": "promo",
                            },
                        }
                    ],
                },
            )
        if request.url.path.endswith("/sendMessage"):
            import json

            sent.append(json.loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    handled = process_bot_updates(db_session, settings=settings, http_client=client)
    assert handled == 1

    join_logs = db_session.scalars(
        select(TelegramNotificationLog).where(
            TelegramNotificationLog.event_type == "subscriber_joined"
        )
    ).all()
    assert join_logs
    assert all(log.chat_id == "10" for log in join_logs)
    assert all(log.chat_id != "20" for log in join_logs)
    assert any("Новый подписчик" in (log.message or "") for log in join_logs)

    sub = db_session.get(TelegramSubscriber, "20")
    assert sub is not None
    assert sub.username == "newbie"
    assert sub.display_name == "New User"


def test_repeat_promo_no_join_alert(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "10", alert_mode=ALERT_MODE_FULL)
    subscribe(db_session, "20", alert_mode=ALERT_MODE_FULL)
    db_session.flush()
    before = db_session.scalar(
        select(func.count())
        .select_from(TelegramNotificationLog)
        .where(TelegramNotificationLog.event_type == "subscriber_joined")
    ) or 0
    sent: list[str] = []
    updates = [{"update_id": 11, "message": {"chat": {"id": 20}, "text": "promo"}}]
    process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client_capturing(updates, sent),
    )
    after = db_session.scalar(
        select(func.count())
        .select_from(TelegramNotificationLog)
        .where(TelegramNotificationLog.event_type == "subscriber_joined")
    ) or 0
    assert after == before
    assert sent
    assert "уже подписаны" in sent[0].lower()


def test_subscribers_list_for_active(db_session: Session) -> None:
    settings = _settings()
    subscribe(db_session, "10", alert_mode=ALERT_MODE_FULL)
    subscribe(db_session, "20", alert_mode=ALERT_MODE_DIGEST)
    db_session.flush()

    row = db_session.get(TelegramSubscriber, "20")
    assert row is not None
    row.username = "alice"
    db_session.flush()

    sent: list[str] = []
    updates = [{"update_id": 12, "message": {"chat": {"id": 10}, "text": "Подписчики"}}]
    handled = process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client_capturing(updates, sent),
    )
    assert handled == 1
    body = sent[0]
    assert "Подписчики: 2" in body
    assert "10" in body
    assert "20" in body
    assert "@alice" in body


def test_subscribers_list_stranger_needs_subscribe(db_session: Session) -> None:
    settings = _settings()
    sent: list[str] = []
    updates = [
        {"update_id": 13, "message": {"chat": {"id": 55}, "text": "/subscribers"}}
    ]
    handled = process_bot_updates(
        db_session,
        settings=settings,
        http_client=_client_capturing(updates, sent),
    )
    assert handled == 1
    assert "подпишитесь" in sent[0].lower()
