"""Telegram alert sender with subscriber fan-out and DB-backed dedup."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import TelegramNotificationLog
from app.services.telegram_subscribers import Audience, list_recipient_chat_ids

logger = logging.getLogger(__name__)

AlertAudience = Literal["events", "digest", "errors"]


def _now() -> datetime:
    return datetime.now(UTC)


def _client_kwargs(settings: Settings) -> dict:
    verify = not bool(settings.telegram_disable_ssl_verify)
    return {"timeout": 30, "verify": verify}


def _post_message(
    *,
    token: str,
    chat_id: str,
    message: str,
    settings: Settings,
    http_client: httpx.Client | None,
) -> str:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message[:4000]}
    try:
        if http_client is not None:
            response = http_client.post(url, json=payload)
            response.raise_for_status()
        else:
            with httpx.Client(**_client_kwargs(settings)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        return "sent"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram send failed chat_id=%s: %s", chat_id, exc)
        return "failed"


def send_to_chat(
    *,
    chat_id: str | int,
    message: str,
    settings: Settings | None = None,
    http_client: httpx.Client | None = None,
) -> str:
    """Direct reply (bot commands). Returns delivery_status."""
    cfg = settings or get_settings()
    token = (cfg.telegram_bot_token or "").strip()
    if not token:
        return "skipped_no_config"
    return _post_message(
        token=token,
        chat_id=str(chat_id),
        message=message,
        settings=cfg,
        http_client=http_client,
    )


def send_alert(
    db: Session,
    *,
    event_type: str,
    dedup_key: str,
    message: str,
    settings: Settings | None = None,
    http_client: httpx.Client | None = None,
    skip_dedup: bool = False,
    audience: AlertAudience = "digest",
) -> TelegramNotificationLog:
    """Broadcast by audience. Returns last log row."""
    cfg = settings or get_settings()
    token = (cfg.telegram_bot_token or "").strip()
    now = _now()
    recipients = list_recipient_chat_ids(db, cfg, audience=audience)

    if not skip_dedup:
        from sqlalchemy import select

        window_start = now - timedelta(seconds=max(0, cfg.telegram_dedup_window_seconds))
        existing = db.scalar(
            select(TelegramNotificationLog)
            .where(
                TelegramNotificationLog.dedup_key == dedup_key,
                TelegramNotificationLog.created_at >= window_start,
                TelegramNotificationLog.delivery_status.in_(("sent", "skipped_dedup")),
            )
            .order_by(TelegramNotificationLog.created_at.desc())
            .limit(1)
        )
        if existing is not None:
            skipped = TelegramNotificationLog(
                event_type=event_type,
                dedup_key=dedup_key,
                chat_id=existing.chat_id or "n/a",
                message=message,
                delivery_status="skipped_dedup",
                created_at=now,
            )
            db.add(skipped)
            db.flush()
            return skipped

    if not token or not recipients:
        skipped = TelegramNotificationLog(
            event_type=event_type,
            dedup_key=dedup_key,
            chat_id=(cfg.telegram_alert_chat_id or "n/a"),
            message=message,
            delivery_status="skipped_no_config",
            created_at=now,
        )
        db.add(skipped)
        db.flush()
        return skipped

    last: TelegramNotificationLog | None = None
    for chat_id in recipients:
        status = _post_message(
            token=token,
            chat_id=chat_id,
            message=message,
            settings=cfg,
            http_client=http_client,
        )
        log = TelegramNotificationLog(
            event_type=event_type,
            dedup_key=dedup_key,
            chat_id=chat_id,
            message=message,
            delivery_status=status,
            created_at=now,
        )
        db.add(log)
        last = log
    db.flush()
    assert last is not None
    return last


# Re-export for type checkers / callers
__all__ = ["AlertAudience", "Audience", "send_alert", "send_to_chat"]
