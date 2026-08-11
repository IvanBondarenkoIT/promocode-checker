"""Hourly ERP reconcile: observe coffee sales, optional auto-close, fraud flags."""

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
    Campaign,
    CampaignStatus,
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    FraudWarningStatus,
    Promocode,
    PromocodeStatus,
    SaleObservation,
)
from app.services.campaign_scope import get_active_kind, in_scope, scoped_promocode_query
from app.services.promocode_close import close_promocode, lock_promocode_by_id
from app.services.sale_evaluation import SaleVerdict, evaluate_orders
from app.services.telegram import send_alert
from app.services.telegram_messages import msg_auto_close, msg_fraud_no_sale, msg_sale_observed

logger = logging.getLogger(__name__)

RECONCILE_POINT_ID = "reconcile"
ENFORCEMENT_MONITOR = "monitor"
ENFORCEMENT_ENFORCE = "enforce"


@dataclass
class ReconcileResult:
    auto_closed: list[str] = field(default_factory=list)
    fraud_warnings: list[str] = field(default_factory=list)
    observed: list[str] = field(default_factory=list)
    qualified_not_closed: list[str] = field(default_factory=list)
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
    for sale in sales:
        if since_aware <= _ensure_aware(sale.sold_at) <= until_aware:
            return True
    return False


def _prior_scan(db: Session, promocode_id) -> CheckerLog | None:
    return db.scalar(
        select(CheckerLog)
        .where(
            CheckerLog.promocode_id == promocode_id,
            CheckerLog.action_type == CheckerActionType.SCAN_CHECK,
        )
        .order_by(CheckerLog.scan_time.desc())
        .limit(1)
    )


def _normalize_enforcement(raw: str) -> str:
    mode = (raw or ENFORCEMENT_MONITOR).strip().lower()
    if mode not in {ENFORCEMENT_MONITOR, ENFORCEMENT_ENFORCE}:
        logger.warning("Unknown PROMO_ENFORCEMENT_MODE=%r; using monitor", raw)
        return ENFORCEMENT_MONITOR
    return mode


def _is_expired(promocode: Promocode, *, now: datetime) -> bool:
    expires_at = promocode.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= now


def _observe_and_maybe_close(
    db: Session,
    *,
    adapter: ErpAdapter,
    settings: Settings,
    now: datetime,
    result: ReconcileResult,
) -> None:
    enforcement = _normalize_enforcement(settings.promo_enforcement_mode)
    min_kg = float(settings.promo_min_coffee_kg)

    active_rows = list(
        db.scalars(
            scoped_promocode_query(db)
            .where(
                Promocode.status == PromocodeStatus.ACTIVE,
                Promocode.expires_at > now,
            )
            .where((Campaign.id.is_(None)) | (Campaign.status != CampaignStatus.CLOSED))
        )
        .unique()
        .all()
    )
    if not active_rows:
        return

    by_promo_customer = {row.customer_erp_id: row for row in active_rows}
    # One ACTIVE code per customer is expected; if several, prefer earliest created.
    for row in active_rows:
        current = by_promo_customer.get(row.customer_erp_id)
        if current is None or _ensure_aware(row.created_at) < _ensure_aware(current.created_at):
            by_promo_customer[row.customer_erp_id] = row

    customer_ids = sorted(by_promo_customer.keys())
    earliest = min(_ensure_aware(row.created_at) for row in active_rows)
    sales = adapter.find_coffee_sales(customer_ids, since=earliest, until=now)
    evaluated = evaluate_orders(sales, min_coffee_kg=min_kg)

    for order in evaluated:
        promo = by_promo_customer.get(order.customer_erp_id)
        if promo is None:
            continue
        created = _ensure_aware(promo.created_at)
        if _ensure_aware(order.sold_at) < created:
            continue

        existing = db.scalar(
            select(SaleObservation.id).where(
                SaleObservation.customer_erp_id == order.customer_erp_id,
                SaleObservation.order_id == order.order_id,
            )
        )
        if existing is not None:
            continue

        closed = False
        if (
            enforcement == ENFORCEMENT_ENFORCE
            and order.verdict == SaleVerdict.QUALIFIED
            and promo.status == PromocodeStatus.ACTIVE
        ):
            locked = lock_promocode_by_id(db, promo.id)
            if locked is not None and locked.status == PromocodeStatus.ACTIVE and not _is_expired(
                locked, now=now
            ):
                prior = _prior_scan(db, locked.id)
                close_promocode(
                    db,
                    locked,
                    action_type=CheckerActionType.AUTO_CLOSE,
                    point_id=RECONCILE_POINT_ID,
                    erp_sale_matched=True,
                    now=now,
                )
                closed = True
                result.auto_closed.append(locked.promocode)
                send_alert(
                    db,
                    event_type="reconcile_auto_close",
                    dedup_key=f"auto_close:{locked.promocode}:{order.order_id}",
                    message=msg_auto_close(
                        code=locked.promocode,
                        customer_erp_id=locked.customer_erp_id,
                        customer_name=order.customer_name,
                        product_name=", ".join(order.products[:3]) if order.products else None,
                        unit_price=order.total_amount,
                        order_id=order.order_id,
                        sold_at=order.sold_at,
                        prior_scan_point_id=prior.point_id if prior else None,
                        prior_scan_at=prior.scan_time if prior else None,
                        tz_name=settings.app_timezone,
                    ),
                    settings=settings,
                    audience="events",
                )
                promo = locked

        observation = SaleObservation(
            promocode_id=promo.id,
            promocode_value=promo.promocode,
            customer_erp_id=order.customer_erp_id,
            customer_name=order.customer_name,
            order_id=order.order_id,
            sold_at=_ensure_aware(order.sold_at),
            order_kg=order.order_kg,
            qty_pieces=order.qty_pieces,
            products=" | ".join(order.products) if order.products else None,
            group_ids=",".join(str(gid) for gid in order.group_ids) if order.group_ids else None,
            total_amount=order.total_amount,
            verdict=order.verdict.value,
            enforcement_mode=enforcement,
            promocode_closed=closed,
            detected_at=now,
            notified_at=now,
        )
        db.add(observation)
        db.flush()
        result.observed.append(order.order_id)
        if order.verdict == SaleVerdict.QUALIFIED and not closed:
            result.qualified_not_closed.append(promo.promocode)

        send_alert(
            db,
            event_type="sale_observed",
            dedup_key=f"sale_obs:{order.customer_erp_id}:{order.order_id}",
            message=msg_sale_observed(
                code=promo.promocode,
                customer_erp_id=order.customer_erp_id,
                customer_name=order.customer_name,
                verdict=order.verdict.value,
                order_kg=order.order_kg,
                min_coffee_kg=min_kg,
                products=order.products,
                order_id=order.order_id,
                sold_at=order.sold_at,
                enforcement_mode=enforcement,
                promocode_closed=closed,
                total_amount=order.total_amount,
                tz_name=settings.app_timezone,
            ),
            settings=settings,
            audience="events",
        )


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

    active_kind = get_active_kind(db)
    candidates: list[tuple[CheckerLog, Promocode]] = []
    for log in manual_logs:
        if log.id in existing_warning_log_ids:
            continue
        if log.promocode_id is None:
            continue
        promo = db.get(Promocode, log.promocode_id)
        if promo is None or promo.redeemed_at is None:
            continue
        if not in_scope(promo, active_kind):
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
            message=msg_fraud_no_sale(
                code=promo.promocode,
                point_id=log.point_id,
                customer_erp_id=promo.customer_erp_id,
                customer_name=None,
                fraud_window_hours=settings.fraud_match_window_hours,
                checked_at=now,
                tz_name=settings.app_timezone,
            ),
            settings=settings,
            audience="events",
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
        _observe_and_maybe_close(db, adapter=erp, settings=cfg, now=current, result=result)
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
                audience="errors",
            )
            db.flush()
        except Exception:  # noqa: BLE001 — never mask original failure
            logger.exception("Failed to send reconcile crash alert")
        raise

    return result
