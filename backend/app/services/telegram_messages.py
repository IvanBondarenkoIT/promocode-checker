"""Russian human-readable Telegram message templates for ops alerts."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.shop_names import shop_label

TZ_DEFAULT = "Asia/Tbilisi"


def format_local(dt: datetime | None, *, tz_name: str = TZ_DEFAULT) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        local = dt.replace(tzinfo=ZoneInfo(tz_name))
    else:
        local = dt.astimezone(ZoneInfo(tz_name))
    return local.strftime("%d.%m.%Y %H:%M")


def customer_line(*, customer_erp_id: str | None, customer_name: str | None = None) -> str:
    cid = (customer_erp_id or "").strip() or "—"
    name = (customer_name or "").strip()
    if name:
        return f"{name} ({cid})"
    return cid


def msg_scan(
    *,
    code: str,
    status_label: str,
    point_id: str,
    when: datetime,
    customer_erp_id: str | None = None,
    customer_name: str | None = None,
    campaign_name: str | None = None,
    tz_name: str = TZ_DEFAULT,
) -> str:
    client = customer_line(customer_erp_id=customer_erp_id, customer_name=customer_name)
    lines = [
        "Скан промокода",
        f"Код: {code} · {status_label}",
        f"Клиент: {client}",
        f"Магазин: {shop_label(point_id)}",
    ]
    if campaign_name:
        lines.append(f"Кампания: {campaign_name}")
    lines.append(f"Время: {format_local(when, tz_name=tz_name)}")
    return "\n".join(lines)


def msg_manual_close(
    *,
    code: str,
    point_id: str,
    when: datetime,
    customer_erp_id: str | None = None,
    customer_name: str | None = None,
    fraud_window_hours: int = 2,
    tz_name: str = TZ_DEFAULT,
) -> str:
    client = customer_line(customer_erp_id=customer_erp_id, customer_name=customer_name)
    return "\n".join(
        [
            "Промокод закрыт вручную",
            f"Код: {code}",
            f"Клиент: {client}",
            f"Магазин: {shop_label(point_id)}",
            f"Дальше: ждём продажу кофе в ERP (~{fraud_window_hours} ч)",
            f"Время: {format_local(when, tz_name=tz_name)}",
        ]
    )


def msg_auto_close(
    *,
    code: str,
    customer_erp_id: str | None,
    customer_name: str | None,
    product_name: str | None,
    unit_price: float | None,
    order_id: str | None,
    sold_at: datetime | None,
    prior_scan_point_id: str | None,
    prior_scan_at: datetime | None,
    tz_name: str = TZ_DEFAULT,
) -> str:
    sold_bits: list[str] = []
    if product_name:
        sold_bits.append(product_name)
    if unit_price is not None:
        sold_bits.append(f"{unit_price:.2f} ₾")
    if order_id:
        sold_bits.append(f"заказ {order_id}")
    sold_line = " · ".join(sold_bits) if sold_bits else "кофе (группа whitelist)"
    client = customer_line(customer_erp_id=customer_erp_id, customer_name=customer_name)

    if prior_scan_at is not None:
        scan_line = (
            f"Скан раньше: да · магазин {shop_label(prior_scan_point_id)} · "
            f"{format_local(prior_scan_at, tz_name=tz_name)}"
        )
    else:
        scan_line = "Скан раньше: нет — кассир не отметил скидку в чекере"

    return "\n".join(
        [
            "Продажа кофе → промокод закрыт автоматически",
            f"Код: {code}",
            f"Клиент: {client}",
            f"Продано: {sold_line}",
            f"Дата продажи: {format_local(sold_at, tz_name=tz_name)}",
            scan_line,
        ]
    )


def msg_fraud_no_sale(
    *,
    code: str,
    point_id: str | None,
    customer_erp_id: str | None,
    customer_name: str | None,
    fraud_window_hours: int,
    checked_at: datetime,
    tz_name: str = TZ_DEFAULT,
) -> str:
    client = customer_line(customer_erp_id=customer_erp_id, customer_name=customer_name)
    return "\n".join(
        [
            "Тревога: ручное закрытие без продажи кофе",
            f"Код: {code}",
            f"Клиент: {client}",
            f"Магазин закрытия: {shop_label(point_id)}",
            f"Окно поиска: ±{fraud_window_hours} ч вокруг закрытия",
            f"Время проверки: {format_local(checked_at, tz_name=tz_name)}",
        ]
    )


def msg_subscribed() -> str:
    return (
        "Вы подписаны на оповещения promocode-checker.\n"
        "Будут приходить сканы, ручные/авто закрытия и тревоги.\n"
        "Отписка: /stop\n"
        "Демо всех типов сообщений: /demo"
    )


def msg_welcome(*, keyword: str) -> str:
    return (
        "Привет! Это бот оповещений DimKava Promo Alerts.\n\n"
        f"Подписаться: напишите «{keyword}»\n"
        "Отписаться: /stop\n"
        "Примеры всех сообщений: /demo"
    )


def msg_unsubscribed() -> str:
    return "Вы отписаны от оповещений promocode-checker."


def msg_already_subscribed() -> str:
    return "Вы уже подписаны. Отписка: /stop · демо: /demo"


def demo_messages(*, tz_name: str = TZ_DEFAULT) -> list[tuple[str, str]]:
    """Return (label, text) samples for visual calibration."""
    from datetime import UTC, timedelta

    now = datetime.now(UTC)
    sold = now - timedelta(hours=2)
    scan_at = now - timedelta(hours=3)
    base = dict(
        code="41000001",
        customer_erp_id="12523",
        customer_name="КЛИЕНТ PALIASHVILI",
        tz_name=tz_name,
    )
    items: list[tuple[str, str]] = [
        (
            "scan_active",
            msg_scan(
                status_label="ACTIVE",
                point_id="IVAN",
                when=now,
                campaign_name="AUTO_CLOSE demo",
                **base,
            ),
        ),
        (
            "scan_used",
            msg_scan(status_label="USED", point_id="IVAN", when=now, **base),
        ),
        (
            "scan_expired",
            msg_scan(status_label="EXPIRED", point_id="IVAN", when=now, **base),
        ),
        (
            "scan_not_found",
            msg_scan(
                code="99999999",
                status_label="NOT FOUND",
                point_id="IVAN",
                when=now,
                customer_erp_id=None,
                customer_name=None,
                tz_name=tz_name,
            ),
        ),
        (
            "manual_close",
            msg_manual_close(point_id="IVAN", when=now, fraud_window_hours=2, **base),
        ),
        (
            "auto_close_with_prior_scan",
            msg_auto_close(
                product_name='Coffee "Blaser" Rosso & Nero (250 g)',
                unit_price=45.0,
                order_id="447720",
                sold_at=sold,
                prior_scan_point_id="IVAN",
                prior_scan_at=scan_at,
                **base,
            ),
        ),
        (
            "auto_close_no_prior_scan",
            msg_auto_close(
                product_name='Coffee "Blaser" Sera (250 g)',
                unit_price=42.5,
                order_id="447621",
                sold_at=sold,
                prior_scan_point_id=None,
                prior_scan_at=None,
                **base,
            ),
        ),
        (
            "fraud",
            msg_fraud_no_sale(
                point_id="IVAN",
                fraud_window_hours=2,
                checked_at=now,
                **base,
            ),
        ),
        ("subscribed", msg_subscribed()),
    ]
    return items
