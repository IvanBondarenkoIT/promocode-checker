"""Shared promocode close logic for cashier redeem and ERP reconcile."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus


class PromocodeAlreadyClosedError(Exception):
    """Promocode is no longer ACTIVE and cannot be closed again."""


def _now() -> datetime:
    return datetime.now(UTC)


def lock_promocode_by_code(db: Session, code: str) -> Promocode | None:
    """Load promocode row with FOR UPDATE (call inside a transaction)."""
    return db.scalar(select(Promocode).where(Promocode.promocode == code).with_for_update())


def lock_promocode_by_id(db: Session, promocode_id: uuid.UUID) -> Promocode | None:
    """Load promocode row with FOR UPDATE (call inside a transaction)."""
    return db.scalar(select(Promocode).where(Promocode.id == promocode_id).with_for_update())


def close_promocode(
    db: Session,
    promocode: Promocode,
    *,
    action_type: CheckerActionType,
    point_id: str,
    erp_sale_matched: bool = False,
    now: datetime | None = None,
) -> CheckerLog:
    """Mark promocode USED and write a close log. Caller must hold row lock."""
    if promocode.status == PromocodeStatus.USED:
        raise PromocodeAlreadyClosedError(promocode.promocode)

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
