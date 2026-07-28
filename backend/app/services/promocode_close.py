"""Shared promocode close logic for cashier redeem and ERP reconcile."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus


def _now() -> datetime:
    return datetime.now(UTC)


def close_promocode(
    db: Session,
    promocode: Promocode,
    *,
    action_type: CheckerActionType,
    point_id: str,
    erp_sale_matched: bool = False,
    now: datetime | None = None,
) -> CheckerLog:
    """Mark promocode USED and write a close log. Caller must ensure it is ACTIVE."""
    current = now or _now()
    promocode.status = PromocodeStatus.USED
    promocode.redeemed_at = current
    log = CheckerLog(
        promocode_id=promocode.id,
        scanned_code=promocode.promocode,
        action_type=action_type,
        point_id=point_id,
        erp_sale_matched=erp_sale_matched,
        scan_time=current,
    )
    db.add(log)
    db.flush()
    return log
