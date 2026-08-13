"""Telegram subscriber list helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.telegram_subscriber import TelegramSubscriber
from app.services.telegram_topics import (
    ALERT_MODE_CUSTOM,
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    DEFAULT_TOPICS_CSV,
    TOPIC_SYSTEM,
    has_topic,
    infer_alert_mode,
    preset_topics,
    toggle_topic,
    topics_to_csv,
)


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
    topic: str | None = None,
) -> list[str]:
    """Recipients for a topic.

    - seed chats always receive every topic
    - active subscribers receive if ``topics`` includes the topic
    - ``topic=None`` means all active subscribers (demo / broadcast)
    - ``system`` is always present in subscriber topics
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

    active = select(TelegramSubscriber).where(TelegramSubscriber.active.is_(True))
    for row in db.scalars(active).all():
        if topic is None or has_topic(row.topics, topic) or topic == TOPIC_SYSTEM:
            add(row.chat_id)

    return out


def is_active_subscriber(db: Session, chat_id: str | int) -> bool:
    row = db.get(TelegramSubscriber, str(chat_id).strip())
    return row is not None and bool(row.active)


def get_subscriber(db: Session, chat_id: str | int) -> TelegramSubscriber | None:
    return db.get(TelegramSubscriber, str(chat_id).strip())


def subscribe(
    db: Session,
    chat_id: str | int,
    *,
    alert_mode: str = ALERT_MODE_FULL,
    topics: str | None = None,
) -> bool:
    """Return True if newly subscribed (or reactivated)."""
    cid = str(chat_id).strip()
    if topics is not None:
        topics_csv = topics_to_csv(topics)
        mode = infer_alert_mode(topics_csv)
    else:
        mode_key = (alert_mode or ALERT_MODE_FULL).strip().lower()
        if mode_key in {ALERT_MODE_FULL, ALERT_MODE_DIGEST}:
            mode = mode_key
            topics_csv = topics_to_csv(preset_topics(mode))
        elif mode_key == ALERT_MODE_CUSTOM:
            mode = ALERT_MODE_CUSTOM
            topics_csv = topics_to_csv(DEFAULT_TOPICS_CSV)
        else:
            # critical / sales presets
            chosen = preset_topics(mode_key)
            topics_csv = topics_to_csv(chosen)
            mode = infer_alert_mode(chosen)

    row = db.get(TelegramSubscriber, cid)
    now = datetime.now(UTC)
    if row is None:
        db.add(
            TelegramSubscriber(
                chat_id=cid,
                active=True,
                alert_mode=mode,
                topics=topics_csv,
                created_at=now,
                updated_at=now,
            )
        )
        db.flush()
        return True
    if not row.active:
        row.active = True
        row.alert_mode = mode
        row.topics = topics_csv
        row.updated_at = now
        db.flush()
        return True
    return False


def set_alert_mode(db: Session, chat_id: str | int, alert_mode: str) -> bool:
    """Apply a preset for an active subscriber. Returns False if not subscribed."""
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    mode_key = (alert_mode or ALERT_MODE_FULL).strip().lower()
    topics_csv = topics_to_csv(preset_topics(mode_key))
    row.topics = topics_csv
    row.alert_mode = infer_alert_mode(topics_csv)
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True


def set_topics(db: Session, chat_id: str | int, topics: str | list[str]) -> bool:
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    topics_csv = topics_to_csv(topics)
    row.topics = topics_csv
    row.alert_mode = infer_alert_mode(topics_csv)
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True


def toggle_subscriber_topic(db: Session, chat_id: str | int, topic: str) -> str | None:
    """Toggle topic; returns new topics CSV or None if not subscribed."""
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return None
    new_csv = toggle_topic(row.topics, topic)
    row.topics = new_csv
    row.alert_mode = infer_alert_mode(new_csv)
    row.updated_at = datetime.now(UTC)
    db.flush()
    return new_csv


def unsubscribe(db: Session, chat_id: str | int) -> bool:
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None or not row.active:
        return False
    row.active = False
    row.updated_at = datetime.now(UTC)
    db.flush()
    return True


def list_active_subscribers(db: Session) -> list[TelegramSubscriber]:
    """Active subscribers, newest first."""
    stmt = (
        select(TelegramSubscriber)
        .where(TelegramSubscriber.active.is_(True))
        .order_by(TelegramSubscriber.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def update_subscriber_profile(
    db: Session,
    chat_id: str | int,
    *,
    username: str | None = None,
    display_name: str | None = None,
) -> None:
    """Best-effort profile sync from Telegram message.from (known chats only)."""
    cid = str(chat_id).strip()
    row = db.get(TelegramSubscriber, cid)
    if row is None:
        return
    changed = False
    if username is not None:
        clean_user = (username or "").strip().lstrip("@")[:64] or None
        if clean_user != row.username:
            row.username = clean_user
            changed = True
    if display_name is not None:
        clean_name = (display_name or "").strip()[:128] or None
        if clean_name != row.display_name:
            row.display_name = clean_name
            changed = True
    if changed:
        row.updated_at = datetime.now(UTC)
        db.flush()


def profile_from_telegram_user(user: dict | None) -> tuple[str | None, str | None]:
    """Extract (username, display_name) from Telegram User object."""
    if not user:
        return None, None
    username = user.get("username")
    username_s = str(username).strip() if username else None
    parts: list[str] = []
    first = user.get("first_name")
    last = user.get("last_name")
    if first:
        parts.append(str(first).strip())
    if last:
        parts.append(str(last).strip())
    display = " ".join(p for p in parts if p) or None
    return username_s, display
