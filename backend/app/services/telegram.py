"""Telegram alert sender with DB-backed dedup."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import TelegramNotificationLog

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def send_alert(
    db: Session,
    *,
    event_type: str,
    dedup_key: str,
    message: str,
    settings: Settings | None = None,
    http_client: httpx.Client | None = None,
) -> TelegramNotificationLog:
    cfg = settings or get_settings()
    chat_id = (cfg.telegram_alert_chat_id or "").strip()
    token = (cfg.telegram_bot_token or "").strip()
    now = _now()

    window_start = now - timedelta(seconds=max(0, cfg.telegram_dedup_window_seconds))
    existing = db.scalar(
        select(TelegramNotificationLog)
        .where(
            TelegramNotificationLog.dedup_key == dedup_key,
            TelegramNotificationLog.created_at >= window_start,
        )
        .order_by(TelegramNotificationLog.created_at.desc())
        .limit(1)
    )
    if existing is not None:
        skipped = TelegramNotificationLog(
            event_type=event_type,
            dedup_key=dedup_key,
            chat_id=chat_id or existing.chat_id or "n/a",
            message=message,
            delivery_status="skipped_dedup",
            created_at=now,
        )
        db.add(skipped)
        db.flush()
        return skipped

    if not token or not chat_id:
        skipped = TelegramNotificationLog(
            event_type=event_type,
            dedup_key=dedup_key,
            chat_id=chat_id or "n/a",
            message=message,
            delivery_status="skipped_no_config",
            created_at=now,
        )
        db.add(skipped)
        db.flush()
        return skipped

    delivery_status = "sent"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message[:4000]}
        if http_client is not None:
            response = http_client.post(url, json=payload)
            response.raise_for_status()
        else:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        delivery_status = "failed"
        logger.warning("Telegram send failed: %s", exc)

    log = TelegramNotificationLog(
        event_type=event_type,
        dedup_key=dedup_key,
        chat_id=chat_id,
        message=message,
        delivery_status=delivery_status,
        created_at=now,
    )
    db.add(log)
    db.flush()
    return log
