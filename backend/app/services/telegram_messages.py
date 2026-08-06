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


def msg_subscribed(*, alert_mode: str = "full") -> str:
    mode_line = (
        "Режим: полный (события + итоги дня)."
        if alert_mode == "full"
        else "Режим: только итоги (старт/конец дня)."
    )
    return (
        "Вы подписаны на оповещения promocode-checker.\n"
        f"{mode_line}\n"
        "Ошибки и сбои приходят всегда.\n"
        "Режимы: /full (полный) · /digest или «итоги»\n"
        "Отписка: /stop · демо: /demo"
    )


def msg_welcome(*, keyword: str) -> str:
    return (
        "Привет! Это бот оповещений DimKava Promo Alerts.\n\n"
        f"Подписаться: напишите «{keyword}» (режим полный)\n"
        "Только итоги дня: /digest\n"
        "Все события: /full\n"
        "Отписаться: /stop\n"
        "Примеры сообщений: /demo"
    )


def msg_unsubscribed() -> str:
    return "Вы отписаны от оповещений promocode-checker."


def msg_already_subscribed() -> str:
    return (
        "Вы уже подписаны.\n"
        "Режимы: /full · /digest · отписка: /stop · демо: /demo"
    )


def msg_mode_set(*, alert_mode: str) -> str:
    if alert_mode == "digest":
        return (
            "Режим: только итоги.\n"
            "Будут старт дня (~10:00), сводка (~22:00) и ошибки.\n"
            "Вернуть события: /full"
        )
    return (
        "Режим: полный.\n"
        "Сканы, закрытия, тревоги + итоги дня + ошибки.\n"
        "Только итоги: /digest"
    )


def msg_need_subscribe() -> str:
    return "Сначала подпишитесь: напишите «promo» (или своё ключевое слово)."


def _sales_summary_lines(
    *,
    sales_count: int,
    sales_sum: float | None,
    top_products: list[tuple[str, int]],
) -> list[str]:
    if sales_count <= 0:
        return ["Продажи кофе (ERP): пока нет"]
    sum_part = f" · сумма ~{sales_sum:.2f} ₾" if sales_sum is not None else ""
    lines = [f"Продажи кофе (ERP): {sales_count} поз.{sum_part}"]
    if top_products:
        lines.append("Топ:")
        for name, count in top_products[:5]:
            lines.append(f"· {name} × {count}")
    return lines


def msg_day_start(
    *,
    local_date: str,
    sales_count: int,
    sales_sum: float | None,
    top_products: list[tuple[str, int]],
) -> str:
    lines = [
        "Рабочий день начался",
        f"Дата: {local_date}",
        *_sales_summary_lines(
            sales_count=sales_count,
            sales_sum=sales_sum,
            top_products=top_products,
        ),
    ]
    return "\n".join(lines)


def msg_day_end(
    *,
    local_date: str,
    sales_count: int,
    sales_sum: float | None,
    top_products: list[tuple[str, int]],
    scan_count: int,
    manual_close_count: int,
    auto_close_count: int,
    fraud_count: int,
    active_campaign_kind: str | None = None,
    campaigns: list[tuple[str, int, int]] | None = None,
) -> str:
    lines = [
        "Итог дня",
        f"Дата: {local_date}",
    ]
    if active_campaign_kind:
        lines.append(f"Режим данных: {active_campaign_kind}")
    lines.extend(
        _sales_summary_lines(
            sales_count=sales_count,
            sales_sum=sales_sum,
            top_products=top_products,
        )
    )
    lines.extend(
        [
            "События чекера:",
            f"· сканы: {scan_count}",
            f"· ручные закрытия: {manual_close_count}",
            f"· автозакрытия: {auto_close_count}",
            f"· тревоги (без продажи): {fraud_count}",
        ]
    )
    if campaigns:
        lines.append("Кампании (выдано/использовано):")
        for name, issued, used in campaigns[:5]:
            lines.append(f"· {name}: {issued}/{used}")
    return "\n".join(lines)


def msg_campaign_import(
    *,
    campaign_code: str,
    campaign_name: str,
    campaign_kind: str,
    created: int,
    skipped: int,
    errors: int,
    dry_run: bool = False,
) -> str:
    head = "Импорт кампании (проверка, без записи)" if dry_run else "Импорт кампании"
    return "\n".join(
        [
            head,
            f"Кампания: {campaign_name} ({campaign_code})",
            f"Тип данных: {campaign_kind}",
            f"Выдано кодов: {created}",
            f"Пропущено (уже были): {skipped}",
            f"Ошибок: {errors}",
        ]
    )


def msg_scope_switched(*, previous: str, current: str, actor: str) -> str:
    return "\n".join(
        [
            "Смена рабочего режима данных",
            f"Было: {previous} → стало: {current}",
            f"Кто: {actor}",
            (
                "Внимание: касса и автозакрытие теперь работают с боевыми кампаниями."
                if current == "LIVE"
                else "Боевые промокоды сейчас не обслуживаются."
            ),
        ]
    )


def msg_digest_error(*, kind: str, detail: str, local_date: str) -> str:
    return "\n".join(
        [
            "Ошибка дневной сводки",
            f"Тип: {kind}",
            f"Дата: {local_date}",
            f"Детали: {detail[:500]}",
        ]
    )


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
        (
            "day_start",
            msg_day_start(
                local_date="04.08.2026",
                sales_count=2,
                sales_sum=87.5,
                top_products=[
                    ('Coffee "Blaser" Rosso & Nero (250 g)', 1),
                    ('Coffee "Blaser" Sera (250 g)', 1),
                ],
            ),
        ),
        (
            "day_end",
            msg_day_end(
                local_date="04.08.2026",
                sales_count=12,
                sales_sum=540.0,
                top_products=[('Coffee "Blaser" Rosso & Nero (250 g)', 5)],
                scan_count=20,
                manual_close_count=3,
                auto_close_count=8,
                fraud_count=1,
                active_campaign_kind="LIVE",
                campaigns=[("Coffee beans 1-2kg", 175, 12)],
            ),
        ),
        (
            "campaign_import",
            msg_campaign_import(
                campaign_code="beans_1_2kg_preprod",
                campaign_name="Coffee beans 1-2kg preprod",
                campaign_kind="LIVE",
                created=175,
                skipped=0,
                errors=0,
            ),
        ),
        (
            "scope_switched",
            msg_scope_switched(previous="TEST", current="LIVE", actor="admin"),
        ),
        ("subscribed", msg_subscribed()),
    ]
    return items
