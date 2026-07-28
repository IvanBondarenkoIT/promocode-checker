"""Hourly ERP reconcile: auto-close ACTIVE and flag unmatched manual closes."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.erp.base import ErpAdapter
from app.integrations.erp.factory import get_erp_adapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.models import (
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    FraudWarningStatus,
    Promocode,
    PromocodeStatus,
)
from app.services.promocode_close import close_promocode, lock_promocode_by_id
from app.services.telegram import send_alert

logger = logging.getLogger(__name__)

RECONCILE_POINT_ID = "reconcile"


@dataclass
class ReconcileResult:
    auto_closed: list[str] = field(default_factory=list)
    fraud_warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _sales_by_customer(
    sales: list[CoffeeSaleMatch],
) -> dict[str, list[CoffeeSaleMatch]]:
    grouped: dict[str, list[CoffeeSaleMatch]] = {}
    for sale in sales:
        grouped.setdefault(sale.customer_erp_id, []).append(sale)
    return grouped


def _has_sale_in_window(
    sales: list[CoffeeSaleMatch],
    *,
    since: datetime,
    until: datetime,
) -> bool:
    since_aware = _ensure_aware(since)
    until_aware = _ensure_aware(until)
    return any(since_aware <= _ensure_aware(sale.sold_at) <= until_aware for sale in sales)


def _auto_close_active(
    db: Session,
    *,
    adapter: ErpAdapter,
    settings: Settings,
    now: datetime,
    result: ReconcileResult,
) -> None:
    active_rows = list(
        db.scalars(
            select(Promocode).where(
                Promocode.status == PromocodeStatus.ACTIVE,
                Promocode.expires_at > now,
            )
        ).all()
    )
    if not active_rows:
        return

    customer_ids = sorted({row.customer_erp_id for row in active_rows})
    earliest = min(_ensure_aware(row.created_at) for row in active_rows)
    sales = adapter.find_coffee_sales(customer_ids, since=earliest, until=now)
    by_customer = _sales_by_customer(sales)

    for promo in active_rows:
        created = _ensure_aware(promo.created_at)
        customer_sales = by_customer.get(promo.customer_erp_id, [])
        if not _has_sale_in_window(customer_sales, since=created, until=now):
            continue

        locked = lock_promocode_by_id(db, promo.id)
        if locked is None or locked.status != PromocodeStatus.ACTIVE:
            continue
        if _is_expired(locked, now=now):
            continue

        close_promocode(
            db,
            locked,
            action_type=CheckerActionType.AUTO_CLOSE,
            point_id=RECONCILE_POINT_ID,
            erp_sale_matched=True,
            now=now,
        )
        result.auto_closed.append(locked.promocode)

        # Decisions: alerts for reconcile changes are mandatory.
        send_alert(
            db,
            event_type="reconcile_auto_close",
            dedup_key=f"auto_close:{locked.promocode}:{now.date().isoformat()}",
            message=(
                f"AUTO_CLOSE promocode={locked.promocode} "
                f"customer_erp_id={locked.customer_erp_id}"
            ),
            settings=settings,
        )


def _is_expired(promocode: Promocode, *, now: datetime) -> bool:
    expires_at = promocode.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= now


def _fraud_check_manual_closes(
    db: Session,
    *,
    adapter: ErpAdapter,
    settings: Settings,
    now: datetime,
    result: ReconcileResult,
) -> None:
    window = timedelta(hours=settings.fraud_match_window_hours)
    amnesty_cutoff = now - window

    manual_logs = list(
        db.scalars(
            select(CheckerLog).where(CheckerLog.action_type == CheckerActionType.MANUAL_CLOSE)
        ).all()
    )
    if not manual_logs:
        return

    existing_warning_log_ids = {
        row
        for row in db.scalars(
            select(FraudWarning.checker_log_id).where(FraudWarning.checker_log_id.is_not(None))
        ).all()
    }

    candidates: list[tuple[CheckerLog, Promocode]] = []
    for log in manual_logs:
        if log.id in existing_warning_log_ids:
            continue
        if log.promocode_id is None:
            continue
        promo = db.get(Promocode, log.promocode_id)
        if promo is None or promo.redeemed_at is None:
            continue
        redeemed_at = _ensure_aware(promo.redeemed_at)
        if redeemed_at > amnesty_cutoff:
            continue
        candidates.append((log, promo))

    if not candidates:
        return

    customer_ids = sorted({promo.customer_erp_id for _, promo in candidates})
    since = min(_ensure_aware(promo.redeemed_at) - window for _, promo in candidates)  # type: ignore[operator]
    until = max(_ensure_aware(promo.redeemed_at) + window for _, promo in candidates)  # type: ignore[operator]
    sales = adapter.find_coffee_sales(customer_ids, since=since, until=max(until, now))
    by_customer = _sales_by_customer(sales)

    for log, promo in candidates:
        redeemed_at = _ensure_aware(promo.redeemed_at)  # type: ignore[arg-type]
        customer_sales = by_customer.get(promo.customer_erp_id, [])
        if _has_sale_in_window(
            customer_sales,
            since=redeemed_at - window,
            until=redeemed_at + window,
        ):
            continue

        warning = FraudWarning(
            promocode_id=promo.id,
            checker_log_id=log.id,
            point_id=log.point_id,
            customer_erp_id=promo.customer_erp_id,
            promocode_value=promo.promocode,
            status=FraudWarningStatus.OPEN,
            message=(
                f"MANUAL_CLOSE without coffee sale in "
                f"{settings.fraud_match_window_hours}h window "
                f"(promocode={promo.promocode}, customer={promo.customer_erp_id})"
            ),
            detected_at=now,
        )
        db.add(warning)
        db.flush()
        result.fraud_warnings.append(promo.promocode)

        send_alert(
            db,
            event_type="fraud_warning",
            dedup_key=f"fraud:{promo.promocode}:{log.id}",
            message=warning.message,
            settings=settings,
        )


def run_reconcile(
    db: Session,
    *,
    settings: Settings | None = None,
    adapter: ErpAdapter | None = None,
    now: datetime | None = None,
) -> ReconcileResult:
    cfg = settings or get_settings()
    current = now or _now()
    erp = adapter or get_erp_adapter(cfg)
    result = ReconcileResult()

    try:
        _auto_close_active(db, adapter=erp, settings=cfg, now=current, result=result)
        _fraud_check_manual_closes(db, adapter=erp, settings=cfg, now=current, result=result)
        db.flush()
    except Exception as exc:
        result.errors.append(str(exc))
        logger.exception("Reconcile job failed")
        try:
            send_alert(
                db,
                event_type="job_crash",
                dedup_key=f"job_crash:reconcile:{current.strftime('%Y%m%d%H')}",
                message=f"Reconcile job failed: {type(exc).__name__}: {exc}",
                settings=cfg,
            )
            db.flush()
        except Exception:  # noqa: BLE001 — never mask original failure
            logger.exception("Failed to send reconcile crash alert")
        raise

    return result
