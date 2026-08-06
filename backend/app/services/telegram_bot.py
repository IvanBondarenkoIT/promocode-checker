"""Poll Telegram getUpdates for subscribe / mode / stop / demo commands."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.telegram_subscriber import (
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    TelegramBotState,
)
from app.services import telegram_messages as msgs
from app.services.telegram import send_alert, send_to_chat
from app.services.telegram_subscribers import set_alert_mode, subscribe, unsubscribe

logger = logging.getLogger(__name__)


def _is_command(text: str, name: str) -> bool:
    t = text.strip().lower()
    return t == name or t.startswith(f"{name}@") or t.startswith(f"{name} ")


def _get_offset(db: Session) -> int:
    row = db.get(TelegramBotState, 1)
    if row is None:
        row = TelegramBotState(id=1, update_offset=0, updated_at=datetime.now(UTC))
        db.add(row)
        db.flush()
    return int(row.update_offset or 0)


def _set_offset(db: Session, offset: int) -> None:
    row = db.get(TelegramBotState, 1)
    if row is None:
        row = TelegramBotState(id=1, update_offset=offset, updated_at=datetime.now(UTC))
        db.add(row)
    else:
        row.update_offset = offset
        row.updated_at = datetime.now(UTC)
    db.flush()


def process_bot_updates(
    db: Session,
    *,
    settings: Settings | None = None,
    timeout: int = 0,
    http_client: httpx.Client | None = None,
) -> int:
    """Process pending updates. Returns number of handled messages."""
    cfg = settings or get_settings()
    token = (cfg.telegram_bot_token or "").strip()
    if not token:
        return 0

    keyword = (cfg.telegram_subscribe_keyword or "promo").strip().lower()
    offset = _get_offset(db)
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": offset, "timeout": timeout}

    try:
        verify = not bool(cfg.telegram_disable_ssl_verify)
        kwargs = {"timeout": max(35, timeout + 5), "verify": verify}
        if http_client is not None:
            response = http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        else:
            with httpx.Client(**kwargs) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram getUpdates failed: %s", exc)
        return 0

    updates = data.get("result") or []
    if not updates:
        return 0

    handled = 0
    max_offset = offset
    for upd in updates:
        upd_id = int(upd.get("update_id", 0))
        max_offset = max(max_offset, upd_id + 1)
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            continue
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        lower = text.lower().strip()
        if _is_command(lower, "/start"):
            send_to_chat(chat_id=chat_id, message=msgs.msg_welcome(keyword=keyword), settings=cfg)
            handled += 1
            continue

        if lower == keyword or lower == f"/{keyword}":
            created = subscribe(db, chat_id, alert_mode=ALERT_MODE_FULL)
            reply = (
                msgs.msg_subscribed(alert_mode=ALERT_MODE_FULL)
                if created
                else msgs.msg_already_subscribed()
            )
            send_to_chat(chat_id=chat_id, message=reply, settings=cfg)
            handled += 1
            continue

        if _is_command(lower, "/full") or lower in {"полный", "full"}:
            ok = set_alert_mode(db, chat_id, ALERT_MODE_FULL)
            if not ok:
                subscribe(db, chat_id, alert_mode=ALERT_MODE_FULL)
            send_to_chat(
                chat_id=chat_id,
                message=msgs.msg_mode_set(alert_mode=ALERT_MODE_FULL),
                settings=cfg,
            )
            handled += 1
            continue

        if (
            _is_command(lower, "/digest")
            or _is_command(lower, "/итоги")
            or lower in {"digest", "итоги"}
        ):
            ok = set_alert_mode(db, chat_id, ALERT_MODE_DIGEST)
            if not ok:
                subscribe(db, chat_id, alert_mode=ALERT_MODE_DIGEST)
            send_to_chat(
                chat_id=chat_id,
                message=msgs.msg_mode_set(alert_mode=ALERT_MODE_DIGEST),
                settings=cfg,
            )
            handled += 1
            continue

        if _is_command(lower, "/stop") or lower in {"stop", "отписаться", "unsubscribe"}:
            removed = unsubscribe(db, chat_id)
            send_to_chat(
                chat_id=chat_id,
                message=msgs.msg_unsubscribed() if removed else "Вы не были в списке подписчиков.",
                settings=cfg,
            )
            handled += 1
            continue

        if _is_command(lower, "/demo") or lower == "demo":
            samples = msgs.demo_messages(tz_name=cfg.app_timezone)
            total = len(samples)
            for index, (label, body) in enumerate(samples, start=1):
                send_to_chat(
                    chat_id=chat_id,
                    message=f"[DEMO {index}/{total} · {label}]\n{body}",
                    settings=cfg,
                )
            handled += 1
            continue

    _set_offset(db, max_offset)
    return handled


def send_demo_to_all_subscribers(db: Session, *, settings: Settings | None = None) -> int:
    """Broadcast DEMO pack to every recipient (calibration CLI)."""
    cfg = settings or get_settings()
    samples = msgs.demo_messages(tz_name=cfg.app_timezone)
    total = len(samples)
    for index, (label, body) in enumerate(samples, start=1):
        send_alert(
            db,
            event_type="ops_demo",
            dedup_key=f"ops_demo:{label}:{datetime.now(UTC).isoformat()}",
            message=f"[DEMO {index}/{total} · {label}]\n{body}",
            settings=cfg,
            skip_dedup=True,
            audience="digest",
        )
    return total
