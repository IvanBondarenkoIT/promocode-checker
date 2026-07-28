from unittest.mock import MagicMock

import httpx
import pytest
from app.core.config import Settings
from app.models import TelegramNotificationLog
from app.services.telegram import send_alert
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
        "TELEGRAM_ALERT_CHAT_ID": "12345",
        "TELEGRAM_DEDUP_WINDOW_SECONDS": "900",
        **overrides,
    }
    return Settings(_env_file=None, **data)


def test_telegram_dedup_skips_second_send(db_session: Session) -> None:
    settings = _settings()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True}))
    client = httpx.Client(transport=transport)

    first = send_alert(
        db_session,
        event_type="fraud_warning",
        dedup_key="fraud:11111111:1",
        message="first",
        settings=settings,
        http_client=client,
    )
    second = send_alert(
        db_session,
        event_type="fraud_warning",
        dedup_key="fraud:11111111:1",
        message="second",
        settings=settings,
        http_client=client,
    )

    assert first.delivery_status == "sent"
    assert second.delivery_status == "skipped_dedup"

    rows = list(db_session.scalars(select(TelegramNotificationLog)).all())
    assert len(rows) == 2


def test_telegram_skips_without_config(db_session: Session) -> None:
    settings = _settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_ALERT_CHAT_ID="")
    client = MagicMock()
    log = send_alert(
        db_session,
        event_type="job_crash",
        dedup_key="crash:1",
        message="boom",
        settings=settings,
        http_client=client,
    )
    assert log.delivery_status == "skipped_no_config"
    client.post.assert_not_called()


def test_telegram_records_failed_delivery(db_session: Session) -> None:
    settings = _settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="fail")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    log = send_alert(
        db_session,
        event_type="reconcile_auto_close",
        dedup_key="auto:1",
        message="closed",
        settings=settings,
        http_client=client,
    )
    assert log.delivery_status == "failed"
