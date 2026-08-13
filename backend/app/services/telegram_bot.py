"""Poll Telegram getUpdates for subscribe / topics / code lookup / demo."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.telegram_subscriber import TelegramBotState
from app.services import telegram_messages as msgs
from app.services.promocode_status import format_status_card, lookup_promocode_status
from app.services.telegram import (
    answer_callback_query,
    edit_message_text,
    send_alert,
    send_to_chat,
)
from app.services.telegram_subscribers import (
    get_subscriber,
    is_active_subscriber,
    set_alert_mode,
    subscribe,
    toggle_subscriber_topic,
    unsubscribe,
)
from app.services.telegram_topics import (
    ALERT_MODE_CRITICAL,
    ALERT_MODE_DIGEST,
    ALERT_MODE_FULL,
    ALERT_MODE_SALES,
    ALL_TOPICS,
    MANDATORY_TOPICS,
    TOPIC_LABELS,
    format_subscriptions_text,
    topics_from_csv,
)

logger = logging.getLogger(__name__)

BTN_MY = "Мои подписки"
BTN_SETUP = "Настроить"
BTN_CHECK = "Проверить код"
BTN_DIGEST = "Итоги дня"
BTN_HELP = "Помощь"

CALLBACK_TOGGLE_PREFIX = "tg_topic:"
CODE_RE = re.compile(r"^\d{8,20}$")


def main_reply_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [
            [{"text": BTN_MY}, {"text": BTN_SETUP}],
            [{"text": BTN_CHECK}],
            [{"text": BTN_DIGEST}, {"text": BTN_HELP}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def topics_inline_keyboard(topics_csv: str | None) -> dict[str, Any]:
    chosen = topics_from_csv(topics_csv)
    rows: list[list[dict[str, str]]] = []
    for topic in ALL_TOPICS:
        if topic in MANDATORY_TOPICS:
            mark = "🔒"
        elif topic in chosen:
            mark = "✅"
        else:
            mark = "⬜"
        rows.append(
            [
                {
                    "text": f"{mark} {TOPIC_LABELS[topic]}",
                    "callback_data": f"{CALLBACK_TOGGLE_PREFIX}{topic}",
                }
            ]
        )
    return {"inline_keyboard": rows}


def topics_settings_text(topics_csv: str | None) -> str:
    return (
        "Настройка оповещений\n"
        "Нажмите тему, чтобы включить или выключить.\n"
        "🔒 Системные — всегда включены.\n\n"
        + format_subscriptions_text(topics_csv)
    )


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


def _reply(
    *,
    chat_id: str | int,
    message: str,
    settings: Settings,
    with_keyboard: bool = True,
    http_client: httpx.Client | None = None,
) -> None:
    send_to_chat(
        chat_id=chat_id,
        message=message,
        settings=settings,
        http_client=http_client,
        reply_markup=main_reply_keyboard() if with_keyboard else None,
    )


def _apply_preset(db: Session, chat_id: str | int, preset: str) -> None:
    ok = set_alert_mode(db, chat_id, preset)
    if not ok:
        subscribe(db, chat_id, alert_mode=preset)


def _handle_code_lookup(
    db: Session,
    *,
    chat_id: str | int,
    code: str,
    settings: Settings,
    http_client: httpx.Client | None = None,
) -> None:
    if not is_active_subscriber(db, chat_id):
        _reply(
            chat_id=chat_id,
            message=msgs.msg_need_subscribe(),
            settings=settings,
            http_client=http_client,
        )
        return
    card = lookup_promocode_status(db, code, settings=settings)
    text = format_status_card(card, tz_name=settings.app_timezone)
    _reply(chat_id=chat_id, message=text, settings=settings, http_client=http_client)


def _handle_callback(
    db: Session,
    *,
    callback: dict[str, Any],
    settings: Settings,
    http_client: httpx.Client | None = None,
) -> bool:
    data = (callback.get("data") or "").strip()
    cq_id = str(callback.get("id") or "")
    msg = callback.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    message_id = msg.get("message_id")
    if chat_id is None:
        return False

    if not data.startswith(CALLBACK_TOGGLE_PREFIX):
        answer_callback_query(
            callback_query_id=cq_id, settings=settings, http_client=http_client
        )
        return False

    topic = data[len(CALLBACK_TOGGLE_PREFIX) :]
    if topic in MANDATORY_TOPICS:
        answer_callback_query(
            callback_query_id=cq_id,
            text="Системные оповещения нельзя отключить",
            settings=settings,
            http_client=http_client,
        )
        return True

    new_csv = toggle_subscriber_topic(db, chat_id, topic)
    if new_csv is None:
        answer_callback_query(
            callback_query_id=cq_id,
            text="Сначала подпишитесь: promo",
            settings=settings,
            http_client=http_client,
        )
        return True

    if message_id is not None:
        edit_message_text(
            chat_id=chat_id,
            message_id=int(message_id),
            message=topics_settings_text(new_csv),
            settings=settings,
            http_client=http_client,
            reply_markup=topics_inline_keyboard(new_csv),
        )
    answer_callback_query(
        callback_query_id=cq_id,
        text=f"{TOPIC_LABELS.get(topic, topic)} обновлено",
        settings=settings,
        http_client=http_client,
    )
    return True


def _handle_text(
    db: Session,
    *,
    chat_id: str | int,
    text: str,
    settings: Settings,
    http_client: httpx.Client | None = None,
) -> bool:
    keyword = (settings.telegram_subscribe_keyword or "promo").strip().lower()
    lower = text.lower().strip()
    raw = text.strip()

    if _is_command(lower, "/start") or lower == BTN_HELP.lower() or lower in {"помощь", "help"}:
        _reply(
            chat_id=chat_id,
            message=msgs.msg_welcome(keyword=keyword),
            settings=settings,
            http_client=http_client,
        )
        return True

    if lower == keyword or lower == f"/{keyword}":
        created = subscribe(db, chat_id, alert_mode=ALERT_MODE_FULL)
        reply = (
            msgs.msg_subscribed(alert_mode=ALERT_MODE_FULL)
            if created
            else msgs.msg_already_subscribed()
        )
        _reply(chat_id=chat_id, message=reply, settings=settings, http_client=http_client)
        return True

    if _is_command(lower, "/full") or lower in {"полный", "full"}:
        _apply_preset(db, chat_id, ALERT_MODE_FULL)
        _reply(
            chat_id=chat_id,
            message=msgs.msg_mode_set(alert_mode=ALERT_MODE_FULL),
            settings=settings,
            http_client=http_client,
        )
        return True

    if (
        _is_command(lower, "/digest")
        or _is_command(lower, "/итоги")
        or lower in {"digest", "итоги"}
        or raw == BTN_DIGEST
    ):
        _apply_preset(db, chat_id, ALERT_MODE_DIGEST)
        _reply(
            chat_id=chat_id,
            message=msgs.msg_mode_set(alert_mode=ALERT_MODE_DIGEST),
            settings=settings,
            http_client=http_client,
        )
        return True

    if _is_command(lower, "/critical") or lower in {"critical", "критичные", "тревоги"}:
        _apply_preset(db, chat_id, ALERT_MODE_CRITICAL)
        _reply(
            chat_id=chat_id,
            message=msgs.msg_mode_set(alert_mode=ALERT_MODE_CRITICAL),
            settings=settings,
            http_client=http_client,
        )
        return True

    if _is_command(lower, "/sales") or lower in {"sales", "продажи"}:
        _apply_preset(db, chat_id, ALERT_MODE_SALES)
        _reply(
            chat_id=chat_id,
            message=msgs.msg_mode_set(alert_mode=ALERT_MODE_SALES),
            settings=settings,
            http_client=http_client,
        )
        return True

    if _is_command(lower, "/stop") or lower in {"stop", "отписаться", "unsubscribe"}:
        removed = unsubscribe(db, chat_id)
        _reply(
            chat_id=chat_id,
            message=msgs.msg_unsubscribed() if removed else "Вы не были в списке подписчиков.",
            settings=settings,
            http_client=http_client,
        )
        return True

    if raw == BTN_MY or _is_command(lower, "/status") or lower in {"подписки", "мои подписки"}:
        sub = get_subscriber(db, chat_id)
        if sub is None or not sub.active:
            _reply(
                chat_id=chat_id,
                message=msgs.msg_need_subscribe(),
                settings=settings,
                http_client=http_client,
            )
            return True
        _reply(
            chat_id=chat_id,
            message=format_subscriptions_text(sub.topics),
            settings=settings,
            http_client=http_client,
        )
        return True

    if raw == BTN_SETUP or _is_command(lower, "/topics") or lower in {"настроить"}:
        sub = get_subscriber(db, chat_id)
        if sub is None or not sub.active:
            _reply(
                chat_id=chat_id,
                message=msgs.msg_need_subscribe(),
                settings=settings,
                http_client=http_client,
            )
            return True
        send_to_chat(
            chat_id=chat_id,
            message=topics_settings_text(sub.topics),
            settings=settings,
            http_client=http_client,
            reply_markup=topics_inline_keyboard(sub.topics),
        )
        return True

    if raw == BTN_CHECK or _is_command(lower, "/code") or lower.startswith("проверить"):
        if _is_command(lower, "/code"):
            parts = raw.split(maxsplit=1)
            if len(parts) < 2 or not CODE_RE.match(parts[1].strip()):
                _reply(
                    chat_id=chat_id,
                    message="Отправьте код: /code 220000012523 или просто 8–20 цифр.",
                    settings=settings,
                    http_client=http_client,
                )
                return True
            _handle_code_lookup(
                db,
                chat_id=chat_id,
                code=parts[1].strip(),
                settings=settings,
                http_client=http_client,
            )
            return True
        _reply(
            chat_id=chat_id,
            message="Отправьте промокод (8–20 цифр) одним сообщением.",
            settings=settings,
            http_client=http_client,
        )
        return True

    if CODE_RE.match(raw):
        _handle_code_lookup(
            db, chat_id=chat_id, code=raw, settings=settings, http_client=http_client
        )
        return True

    if _is_command(lower, "/demo") or lower == "demo":
        samples = msgs.demo_messages(tz_name=settings.app_timezone)
        total = len(samples)
        for index, (label, body) in enumerate(samples, start=1):
            send_to_chat(
                chat_id=chat_id,
                message=f"[DEMO {index}/{total} · {label}]\n{body}",
                settings=settings,
                http_client=http_client,
            )
        return True

    return False


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

        callback = upd.get("callback_query")
        if callback:
            if _handle_callback(
                db, callback=callback, settings=cfg, http_client=http_client
            ):
                handled += 1
            continue

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

        if _handle_text(
            db, chat_id=chat_id, text=text, settings=cfg, http_client=http_client
        ):
            handled += 1

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
            topic=None,
        )
    return total
