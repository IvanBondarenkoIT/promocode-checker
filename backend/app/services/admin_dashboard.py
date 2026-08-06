from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CheckerActionType,
    CheckerLog,
    FraudWarning,
    FraudWarningStatus,
    Promocode,
    PromocodeStatus,
    TelegramNotificationLog,
)
from app.schemas.admin import DashboardResponse
from app.services.campaign_scope import get_active_kind, scoped_promocode_query


def _now() -> datetime:
    return datetime.now(UTC)


def get_dashboard(db: Session) -> DashboardResponse:
    now = _now()
    since = now - timedelta(hours=24)
    active_kind = get_active_kind(db)

    def _count_scoped(*conditions) -> int:
        query = scoped_promocode_query(db, kind=active_kind).where(*conditions)
        return len(set(db.scalars(query).unique().all()))

    active = _count_scoped(Promocode.status == PromocodeStatus.ACTIVE)
    used = _count_scoped(Promocode.status == PromocodeStatus.USED)
    expired = _count_scoped(
        Promocode.status == PromocodeStatus.ACTIVE,
        Promocode.expires_at <= now,
    )
    scans_24h = db.scalar(
        select(func.count())
        .select_from(CheckerLog)
        .where(CheckerLog.scan_time >= since)
    ) or 0
    auto_closes = db.scalar(
        select(func.count())
        .select_from(CheckerLog)
        .where(CheckerLog.action_type == CheckerActionType.AUTO_CLOSE)
    ) or 0
    fraud_open = db.scalar(
        select(func.count())
        .select_from(FraudWarning)
        .where(FraudWarning.status == FraudWarningStatus.OPEN)
    ) or 0
    telegram_24h = db.scalar(
        select(func.count())
        .select_from(TelegramNotificationLog)
        .where(
            TelegramNotificationLog.created_at >= since,
            TelegramNotificationLog.delivery_status == "sent",
        )
    ) or 0

    return DashboardResponse(
        promocodes_active=active,
        promocodes_used=used,
        promocodes_expired=expired,
        scans_last_24h=scans_24h,
        auto_closes_total=auto_closes,
        fraud_open=fraud_open,
        telegram_sent_last_24h=telegram_24h,
        active_campaign_kind=active_kind.value,
    )
