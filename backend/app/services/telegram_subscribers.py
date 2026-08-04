"""Telegram subscriber list helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.telegram_subscriber import TelegramSubscriber


def parse_extra_chat_ids(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
    return parts


def list_recipient_chat_ids(db: Session, settings: Settings) -> list[str]:
    """Active subscribers ∪ TELEGRAM_ALERT_CHAT_ID ∪ TELEGRAM_CHAT_IDS."""
    seen: set[str] = set()
    out: list[str] = []

    def add(cid: str) -> None:
        value = cid.strip()
        if not value or value in seen:
            return
        seen.add(value)
        out.append(value)

    add(settings.telegram_alert_chat_id or "")
    for cid in parse_extra_chat_ids(getattr(settings, "telegram_chat_ids", "") or ""):
        add(cid)

    rows = db.scalars(
        select(TelegramSubscriber).where(TelegramSubscriber.active.is_(True))
    ).all()
    for row in rows:
        add(row.chat_id)

    return out


def subscribe(db: Session, chat_id: str | int) -> bool:
    """Return True if newly subscribed (or reactivated)."""
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    now = datetime.now(UTC)
    if row is None:
        db.add(TelegramSubscriber(chat_id=cid, active=True, created_at=now, updated_at=now))
        db.flush()
        return True
    if not row.active:
        row.active = True
        row.updated_at = now
        db.flush()
        return True
    return False


def unsubscribe(db: Session, chat_id: str | int) -> bool:
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    row.active = False
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True
