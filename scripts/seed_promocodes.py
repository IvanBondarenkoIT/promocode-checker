"""Seed dummy promocodes for local cashier/admin testing."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Promocode, PromocodeStatus  # noqa: E402
from app.services.promocode_generator import calculate_expires_at  # noqa: E402


@dataclass(frozen=True)
class DummyPromocode:
    customer_erp_id: str
    promocode: str
    status: PromocodeStatus
    note: str
    expires_offset_days: int | None = None
    redeemed: bool = False


# Fixed codes for predictable local testing (scan / admin browse).
DUMMY_PROMOCODES: tuple[DummyPromocode, ...] = (
    DummyPromocode("DEMO-ACTIVE-1", "10000001", PromocodeStatus.ACTIVE, "ACTIVE - redeem OK"),
    DummyPromocode("DEMO-ACTIVE-2", "10000002", PromocodeStatus.ACTIVE, "ACTIVE - redeem OK"),
    DummyPromocode("DEMO-ACTIVE-3", "10000003", PromocodeStatus.ACTIVE, "ACTIVE - redeem OK"),
    DummyPromocode("DEMO-USED-1", "20000001", PromocodeStatus.USED, "USED - already closed", redeemed=True),
    DummyPromocode("DEMO-USED-2", "20000002", PromocodeStatus.USED, "USED - already closed", redeemed=True),
    DummyPromocode(
        "DEMO-EXPIRED-1",
        "30000001",
        PromocodeStatus.ACTIVE,
        "EXPIRED — past TTL",
        expires_offset_days=-1,
    ),
    DummyPromocode(
        "DEMO-EXPIRED-2",
        "30000002",
        PromocodeStatus.ACTIVE,
        "EXPIRED — past TTL",
        expires_offset_days=-7,
    ),
)


def upsert_dummy(db, item: DummyPromocode, *, ttl_days: int) -> Promocode:
    existing = db.scalar(select(Promocode).where(Promocode.promocode == item.promocode))
    if existing is not None:
        return existing

    now = datetime.now(UTC)
    if item.expires_offset_days is not None:
        expires_at = now + timedelta(days=item.expires_offset_days)
        created_at = expires_at - timedelta(days=ttl_days)
    else:
        created_at = now
        expires_at = calculate_expires_at(created_at, ttl_days)

    promocode = Promocode(
        customer_erp_id=item.customer_erp_id,
        promocode=item.promocode,
        status=item.status,
        created_at=created_at,
        expires_at=expires_at,
        redeemed_at=now if item.redeemed else None,
    )
    db.add(promocode)
    db.flush()
    return promocode


def main() -> None:
    settings = get_settings()
    printed: list[tuple[DummyPromocode, str, str, str]] = []
    with SessionLocal() as db:
        for item in DUMMY_PROMOCODES:
            row = upsert_dummy(db, item, ttl_days=settings.promocode_ttl_days)
            printed.append((item, row.promocode, row.status.value, row.customer_erp_id))
        db.commit()

    print("Dummy promocodes for local testing:")
    print(f"{'code':<10}\t{'status':<8}\t{'customer':<16}\tnote")
    for item, code, status, customer in printed:
        print(f"{code:<10}\t{status:<8}\t{customer:<16}\t{item.note}")
    print()
    print("NOT_FOUND test: scan any other 8-digit code, e.g. 99999999")


if __name__ == "__main__":
    main()
