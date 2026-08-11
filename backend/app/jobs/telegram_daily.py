"""Daily Telegram digests: day-start (~10:00) and end-of-day (~22:00)."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.erp.base import ErpAdapter
from app.integrations.erp.factory import get_erp_adapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.models import (
    Campaign,
    CheckerLog,
    FraudWarning,
    Promocode,
    PromocodeStatus,
    SaleObservation,
)
from app.models.enums import CheckerActionType
from app.models.telegram_subscriber import TelegramDigestState
from app.services import telegram_messages as msgs
from app.services.campaign_scope import get_active_kind
from app.services.sale_evaluation import SaleVerdict
from app.services.telegram import send_alert

logger = logging.getLogger(__name__)


@dataclass
class DailyDigestResult:
    day_start_sent: bool = False
    eod_sent: bool = False
    errors: list[str] = field(default_factory=list)


def _local_now(settings: Settings, now: datetime | None) -> datetime:
    tz = ZoneInfo(settings.app_timezone)
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(tz)


def _local_day_bounds(local_now: datetime) -> tuple[datetime, datetime, date]:
    """Return (day_start_utc_aware_local, day_end, local_date).

    Bounds are timezone-aware datetimes in the app timezone.
    """
    local_date = local_now.date()
    start = datetime.combine(local_date, time.min, tzinfo=local_now.tzinfo)
    end = datetime.combine(local_date, time.max.replace(microsecond=0), tzinfo=local_now.tzinfo)
    return start, end, local_date


def _past_schedule(local_now: datetime, hour: int, minute: int) -> bool:
    return (local_now.hour, local_now.minute) >= (hour, minute)


def _get_digest_state(db: Session) -> TelegramDigestState:
    row = db.get(TelegramDigestState, 1)
    if row is None:
        row = TelegramDigestState(id=1)
        db.add(row)
        db.flush()
    return row


def _aggregate_sales(
    sales: list[CoffeeSaleMatch],
) -> tuple[int, float | None, list[tuple[str, int]]]:
    count = len(sales)
    prices = [s.unit_price for s in sales if s.unit_price is not None]
    sales_sum = float(sum(prices)) if prices else None
    counter: Counter[str] = Counter()
    for sale in sales:
        name = (sale.product_name or "").strip() or f"group {sale.group_id}"
        counter[name] += 1
    top = counter.most_common(5)
    return count, sales_sum, top


def _fetch_day_sales(
    adapter: ErpAdapter,
    *,
    since: datetime,
    until: datetime,
    settings: Settings,
) -> list[CoffeeSaleMatch]:
    return adapter.find_coffee_sales(
        [],
        since=since,
        until=until,
        all_customers=True,
        row_limit=max(1, settings.telegram_digest_sales_row_limit),
    )


def _checker_counts(
    db: Session, *, since: datetime, until: datetime
) -> tuple[int, int, int]:
    rows = db.execute(
        select(CheckerLog.action_type, func.count())
        .where(CheckerLog.scan_time >= since, CheckerLog.scan_time <= until)
        .group_by(CheckerLog.action_type)
    ).all()
    by_type = {action: int(n) for action, n in rows}
    return (
        by_type.get(CheckerActionType.SCAN_CHECK, 0),
        by_type.get(CheckerActionType.MANUAL_CLOSE, 0),
        by_type.get(CheckerActionType.AUTO_CLOSE, 0),
    )


def _fraud_count(db: Session, *, since: datetime, until: datetime) -> int:
    n = db.scalar(
        select(func.count())
        .select_from(FraudWarning)
        .where(FraudWarning.detected_at >= since, FraudWarning.detected_at <= until)
    )
    return int(n or 0)


def _observation_counts(db: Session, *, since: datetime, until: datetime) -> tuple[int, int]:
    total = db.scalar(
        select(func.count())
        .select_from(SaleObservation)
        .where(SaleObservation.detected_at >= since, SaleObservation.detected_at <= until)
    )
    qualified = db.scalar(
        select(func.count())
        .select_from(SaleObservation)
        .where(
            SaleObservation.detected_at >= since,
            SaleObservation.detected_at <= until,
            SaleObservation.verdict == SaleVerdict.QUALIFIED.value,
        )
    )
    return int(total or 0), int(qualified or 0)


def _campaign_totals(db: Session, kind) -> list[tuple[str, int, int]]:
    rows = db.execute(
        select(
            Campaign.name,
            func.count(Promocode.id),
            func.count(Promocode.id).filter(Promocode.status == PromocodeStatus.USED),
        )
        .join(Promocode, Promocode.campaign_id == Campaign.id)
        .where(Campaign.kind == kind)
        .group_by(Campaign.name)
        .order_by(func.count(Promocode.id).desc())
    ).all()
    return [(name, int(issued or 0), int(used or 0)) for name, issued, used in rows]


def _format_local_date(local_date: date) -> str:
    return local_date.strftime("%d.%m.%Y")


def run_telegram_daily(
    db: Session,
    *,
    settings: Settings | None = None,
    adapter: ErpAdapter | None = None,
    now: datetime | None = None,
    http_client=None,
) -> DailyDigestResult:
    """Send due digests once per local calendar day. Idempotent via digest state."""
    cfg = settings or get_settings()
    local_now = _local_now(cfg, now)
    day_start, day_end, local_date = _local_day_bounds(local_now)
    state = _get_digest_state(db)
    active_kind = get_active_kind(db)
    result = DailyDigestResult()
    erp = adapter or get_erp_adapter(cfg)
    date_label = _format_local_date(local_date)

    # Day start + morning sales
    if (
        _past_schedule(local_now, cfg.telegram_day_start_hour, cfg.telegram_day_start_minute)
        and state.last_day_start_on != local_date
    ):
        try:
            sales = _fetch_day_sales(
                erp, since=day_start, until=local_now, settings=cfg
            )
            count, sales_sum, top = _aggregate_sales(sales)
            send_alert(
                db,
                event_type="day_start",
                dedup_key=f"day_start:{local_date.isoformat()}",
                message=msgs.msg_day_start(
                    local_date=date_label,
                    sales_count=count,
                    sales_sum=sales_sum,
                    top_products=top,
                ),
                settings=cfg,
                audience="digest",
                http_client=http_client,
                skip_dedup=True,
            )
            state.last_day_start_on = local_date
            state.updated_at = datetime.now(UTC)
            db.flush()
            result.day_start_sent = True
        except Exception as exc:  # noqa: BLE001
            detail = f"{type(exc).__name__}: {exc}"
            result.errors.append(detail)
            logger.exception("Day-start digest failed")
            try:
                send_alert(
                    db,
                    event_type="digest_error",
                    dedup_key=f"digest_error:day_start:{local_date.isoformat()}",
                    message=msgs.msg_digest_error(
                        kind="day_start",
                        detail=detail,
                        local_date=date_label,
                    ),
                    settings=cfg,
                    audience="errors",
                    http_client=http_client,
                )
                db.flush()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to send day-start digest error alert")

    # End of day
    if (
        _past_schedule(local_now, cfg.telegram_eod_hour, cfg.telegram_eod_minute)
        and state.last_eod_on != local_date
    ):
        try:
            sales = _fetch_day_sales(erp, since=day_start, until=day_end, settings=cfg)
            count, sales_sum, top = _aggregate_sales(sales)
            scan_n, manual_n, auto_n = _checker_counts(db, since=day_start, until=day_end)
            fraud_n = _fraud_count(db, since=day_start, until=day_end)
            obs_n, qual_n = _observation_counts(db, since=day_start, until=day_end)
            send_alert(
                db,
                event_type="day_end",
                dedup_key=f"day_end:{local_date.isoformat()}",
                message=msgs.msg_day_end(
                    local_date=date_label,
                    sales_count=count,
                    sales_sum=sales_sum,
                    top_products=top,
                    scan_count=scan_n,
                    manual_close_count=manual_n,
                    auto_close_count=auto_n,
                    fraud_count=fraud_n,
                    active_campaign_kind=active_kind.value,
                    campaigns=_campaign_totals(db, active_kind),
                    observations_count=obs_n,
                    qualified_observations_count=qual_n,
                    enforcement_mode=(cfg.promo_enforcement_mode or "monitor").strip().lower(),
                ),
                settings=cfg,
                audience="digest",
                http_client=http_client,
                skip_dedup=True,
            )
            state.last_eod_on = local_date
            state.updated_at = datetime.now(UTC)
            db.flush()
            result.eod_sent = True
        except Exception as exc:  # noqa: BLE001
            detail = f"{type(exc).__name__}: {exc}"
            result.errors.append(detail)
            logger.exception("EOD digest failed")
            try:
                send_alert(
                    db,
                    event_type="digest_error",
                    dedup_key=f"digest_error:day_end:{local_date.isoformat()}",
                    message=msgs.msg_digest_error(
                        kind="day_end",
                        detail=detail,
                        local_date=date_label,
                    ),
                    settings=cfg,
                    audience="errors",
                    http_client=http_client,
                )
                db.flush()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to send EOD digest error alert")

    return result
