from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from app.core.config import Settings
from app.models import CheckerLog, Promocode, PromocodeStatus, TelegramNotificationLog
from app.services.telegram_bot import main_reply_keyboard, process_bot_updates
from app.services.telegram_subscribers import subscribe
from app.services.telegram_topics import ALERT_MODE_FULL
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
