"""Telegram subscriber list helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.telegram_subscriber import (
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    TelegramSubscriber,
)

Audience = Literal["events", "digest", "errors"]


def parse_extra_chat_ids(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
    return parts


def seed_chat_ids(settings: Settings) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    def add(cid: str) -> None:
        value = cid.strip()
        if not value or value in seen:
            return
        seen.add(value)
        out.append(value)

    add(settings.telegram_alert_chat_id or "")
    for cid in parse_extra_chat_ids(getattr(settings, "telegram_chat_ids", "") or ""):
        add(cid)
    return out


def list_recipient_chat_ids(
    db: Session,
    settings: Settings,
    *,
    audience: Audience = "digest",
) -> list[str]:
    """Recipients by audience.

    - events: active alert_mode=full ∪ seed chats (seeds always get events)
    - digest / errors: all active ∪ seed chats
    """
    seen: set[str] = set()
    out: list[str] = []

    def add(cid: str) -> None:
        value = cid.strip()
        if not value or value in seen:
            return
        seen.add(value)
        out.append(value)

    for cid in seed_chat_ids(settings):
        add(cid)

    stmt = select(TelegramSubscriber).where(TelegramSubscriber.active.is_(True))
    if audience == "events":
        stmt = stmt.where(TelegramSubscriber.alert_mode == ALERT_MODE_FULL)

    for row in db.scalars(stmt).all():
        add(row.chat_id)

    return out


def subscribe(
    db: Session,
    chat_id: str | int,
    *,
    alert_mode: str = ALERT_MODE_FULL,
) -> bool:
    """Return True if newly subscribed (or reactivated)."""
    cid = str(chat_id).strip()
    mode = alert_mode if alert_mode in {ALERT_MODE_FULL, ALERT_MODE_DIGEST} else ALERT_MODE_FULL
    row = db.get(TelegramSubscriber, cid)
    now = datetime.now(UTC)
    if row is None:
        db.add(
            TelegramSubscriber(
                chat_id=cid,
                active=True,
                alert_mode=mode,
                created_at=now,
                updated_at=now,
            )
        )
        db.flush()
        return True
    if not row.active:
        row.active = True
        row.alert_mode = mode
        row.updated_at = now
        db.flush()
        return True
    return False


def set_alert_mode(db: Session, chat_id: str | int, alert_mode: str) -> bool:
    """Set mode for an active subscriber. Returns False if not subscribed."""
    cid = str(chat_id).strip()
    mode = alert_mode if alert_mode in {ALERT_MODE_FULL, ALERT_MODE_DIGEST} else ALERT_MODE_FULL
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    row.alert_mode = mode
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True


def unsubscribe(db: Session, chat_id: str | int) -> bool:
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    row.active = False
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True
