"""Read-only promocode status for Telegram bot lookup (no checker logs / alerts)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings, get_settings
from app.models import (
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    FraudWarningStatus,
    Promocode,
    PromocodeStatus,
    SaleObservation,
)
from app.services.campaign_scope import get_active_kind, in_scope
from app.services.promocode_generator import is_valid_promocode
from app.services.shop_names import shop_label
from app.services.telegram_messages import customer_line, format_local


class PromocodeLookupState(StrEnum):
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_FOUND = "NOT_FOUND"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CLOSED_AUTO = "CLOSED_AUTO"
    CLOSED_MANUAL_CONFIRMED = "CLOSED_MANUAL_CONFIRMED"
    CLOSED_MANUAL_WAITING = "CLOSED_MANUAL_WAITING"
    CLOSED_MANUAL_NO_SALE = "CLOSED_MANUAL_NO_SALE"


@dataclass
class PromocodeStatusCard:
    state: PromocodeLookupState
    code: str
    out_of_scope: bool = False
    active_kind: str | None = None
    campaign_kind: str | None = None
    campaign_name: str | None = None
    customer_erp_id: str | None = None
    customer_name: str | None = None
    expires_at: datetime | None = None
    redeemed_at: datetime | None = None
    close_point_id: str | None = None
    erp_sale_matched: bool = False
    fraud_open: bool = False
    waiting_hours_left: float | None = None
    order_id: str | None = None
    order_kg: float | None = None
    sold_at: datetime | None = None


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _is_expired(promocode: Promocode, *, now: datetime) -> bool:
    return _ensure_aware(promocode.expires_at) <= now


def _latest_close_log(db: Session, promocode_id) -> CheckerLog | None:
    return db.scalar(
        select(CheckerLog)
        .where(
            CheckerLog.promocode_id == promocode_id,
            CheckerLog.action_type.in_(
                (CheckerActionType.MANUAL_CLOSE, CheckerActionType.AUTO_CLOSE)
            ),
        )
        .order_by(CheckerLog.scan_time.desc())
        .limit(1)
    )


def _open_fraud(db: Session, promocode_id) -> FraudWarning | None:
    return db.scalar(
        select(FraudWarning)
        .where(
            FraudWarning.promocode_id == promocode_id,
            FraudWarning.status == FraudWarningStatus.OPEN,
        )
        .order_by(FraudWarning.detected_at.desc())
        .limit(1)
    )


def _latest_observation(db: Session, customer_erp_id: str) -> SaleObservation | None:
    return db.scalar(
        select(SaleObservation)
        .where(SaleObservation.customer_erp_id == customer_erp_id)
        .order_by(SaleObservation.detected_at.desc())
        .limit(1)
    )


def lookup_promocode_status(
    db: Session,
    code: str,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> PromocodeStatusCard:
    """Resolve promocode status without writing logs or sending alerts."""
    cfg = settings or get_settings()
    current = now or _now()
    raw = (code or "").strip()
    active_kind = get_active_kind(db)

    if not is_valid_promocode(raw):
        return PromocodeStatusCard(state=PromocodeLookupState.INVALID_FORMAT, code=raw)

    promo = db.scalar(
        select(Promocode).options(joinedload(Promocode.campaign)).where(Promocode.promocode == raw)
    )
    if promo is None:
        return PromocodeStatusCard(state=PromocodeLookupState.NOT_FOUND, code=raw)

    campaign = promo.campaign
    out_of_scope = not in_scope(promo, active_kind)
    base = PromocodeStatusCard(
        state=PromocodeLookupState.ACTIVE,
        code=raw,
        out_of_scope=out_of_scope,
        active_kind=active_kind.value,
        campaign_kind=campaign.kind.value if campaign is not None else None,
        campaign_name=campaign.name if campaign is not None else None,
        customer_erp_id=promo.customer_erp_id,
        customer_name=promo.customer_name,
        expires_at=promo.expires_at,
        redeemed_at=promo.redeemed_at,
    )

    if promo.status == PromocodeStatus.ACTIVE:
        if _is_expired(promo, now=current):
            base.state = PromocodeLookupState.EXPIRED
        else:
            base.state = PromocodeLookupState.ACTIVE
        return base

    # USED
    close_log = _latest_close_log(db, promo.id)
    if close_log is not None:
        base.close_point_id = close_log.point_id
        base.erp_sale_matched = bool(close_log.erp_sale_matched)
        if close_log.action_type == CheckerActionType.AUTO_CLOSE:
            base.state = PromocodeLookupState.CLOSED_AUTO
            obs = _latest_observation(db, promo.customer_erp_id)
            if obs is not None:
                base.order_id = obs.order_id
                base.order_kg = obs.order_kg
                base.sold_at = obs.sold_at
            return base

        # MANUAL_CLOSE
        if close_log.erp_sale_matched:
            base.state = PromocodeLookupState.CLOSED_MANUAL_CONFIRMED
            obs = _latest_observation(db, promo.customer_erp_id)
            if obs is not None:
                base.order_id = obs.order_id
                base.order_kg = obs.order_kg
                base.sold_at = obs.sold_at
            return base

        fraud = _open_fraud(db, promo.id)
        if fraud is not None:
            base.state = PromocodeLookupState.CLOSED_MANUAL_NO_SALE
            base.fraud_open = True
            return base

        redeemed = _ensure_aware(promo.redeemed_at or close_log.scan_time)
        window = timedelta(hours=cfg.fraud_match_window_hours)
        deadline = redeemed + window
        hours_left = max(0.0, (deadline - current).total_seconds() / 3600.0)
        base.state = PromocodeLookupState.CLOSED_MANUAL_WAITING
        base.waiting_hours_left = hours_left
        return base

    # USED without close log (admin path) — treat as confirmed used
    base.state = PromocodeLookupState.CLOSED_MANUAL_CONFIRMED
    return base


def format_status_card(card: PromocodeStatusCard, *, tz_name: str = "Asia/Tbilisi") -> str:
    client = customer_line(
        customer_erp_id=card.customer_erp_id,
        customer_name=card.customer_name,
    )
    lines: list[str] = []

    titles = {
        PromocodeLookupState.INVALID_FORMAT: "Код: неверный формат (нужно 8–20 цифр)",
        PromocodeLookupState.NOT_FOUND: "Код не найден",
        PromocodeLookupState.ACTIVE: "Промокод активен",
        PromocodeLookupState.EXPIRED: "Промокод просрочен",
        PromocodeLookupState.CLOSED_AUTO: "Успешно закрыт автоматически (продажа в ERP)",
        PromocodeLookupState.CLOSED_MANUAL_CONFIRMED: (
            "Успешно закрыт вручную, продажа в ERP подтверждена"
        ),
        PromocodeLookupState.CLOSED_MANUAL_WAITING: (
            "Закрыт вручную — ждём подтверждения покупки в ERP"
        ),
        PromocodeLookupState.CLOSED_MANUAL_NO_SALE: (
            "Закрыт вручную без продажи — открыта тревога"
        ),
    }
    lines.append(titles[card.state])
    lines.append(f"Код: {card.code or '—'}")

    if card.state not in {
        PromocodeLookupState.INVALID_FORMAT,
        PromocodeLookupState.NOT_FOUND,
    }:
        lines.append(f"Клиент: {client}")
        if card.campaign_name:
            kind = card.campaign_kind or "—"
            lines.append(f"Кампания: {card.campaign_name} ({kind})")
        if card.out_of_scope and card.active_kind:
            lines.append(f"⚠ Другая кампания (сейчас активен режим {card.active_kind})")
        if card.expires_at is not None:
            lines.append(f"Действует до: {format_local(card.expires_at, tz_name=tz_name)}")
        if card.redeemed_at is not None:
            lines.append(f"Закрыт: {format_local(card.redeemed_at, tz_name=tz_name)}")
        if card.close_point_id:
            lines.append(f"Магазин: {shop_label(card.close_point_id)}")
        if card.order_id:
            kg = f"{card.order_kg:.2f} кг" if card.order_kg is not None else "? кг"
            lines.append(f"Заказ ERP: {card.order_id} · {kg}")
        if card.sold_at is not None:
            lines.append(f"Дата продажи: {format_local(card.sold_at, tz_name=tz_name)}")
        if card.state == PromocodeLookupState.CLOSED_MANUAL_WAITING:
            if card.waiting_hours_left is not None and card.waiting_hours_left > 0:
                lines.append(f"Осталось окна: ~{card.waiting_hours_left:.1f} ч")
            else:
                lines.append("Окно антифрода истекло — ждём очередной прогон reconcile")

    return "\n".join(lines)
