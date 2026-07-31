"""Seed dummy promocodes for local / server cashier testing."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# Docker exec: build DATABASE_URL from POSTGRES_* (same as entrypoint).
if not os.getenv("DATABASE_URL") and os.getenv("POSTGRES_PASSWORD"):
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "promocode_checker")
    os.environ["DATABASE_URL"] = (
        f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"
    )

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Promocode, PromocodeStatus  # noqa: E402
from app.services.campaign_import import upsert_campaign  # noqa: E402
from app.services.promocode_generator import calculate_expires_at  # noqa: E402
from sqlalchemy import select  # noqa: E402

DEMO_CAMPAIGN_CODE = "DEMO_LOCAL"
DEMO_CAMPAIGN_NAME = "Local demo wave"


@dataclass(frozen=True)
class DummyPromocode:
    customer_erp_id: str
    promocode: str
    status: PromocodeStatus
    note: str
    expires_offset_days: int | None = None
    redeemed: bool = False


def _build_dummy_list() -> tuple[DummyPromocode, ...]:
    active = tuple(
        DummyPromocode(
            f"DEMO-ACTIVE-{i}",
            f"{10_000_000 + i}",
            PromocodeStatus.ACTIVE,
            "ACTIVE - redeem OK",
        )
        for i in range(1, 21)
    )
    used = (
        DummyPromocode(
            "DEMO-USED-1", "20000001", PromocodeStatus.USED, "USED - already closed", redeemed=True
        ),
        DummyPromocode(
            "DEMO-USED-2", "20000002", PromocodeStatus.USED, "USED - already closed", redeemed=True
        ),
    )
    expired = (
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
    return active + used + expired


# Fixed codes for predictable testing (scan / admin browse / barcode PNGs).
DUMMY_PROMOCODES: tuple[DummyPromocode, ...] = _build_dummy_list()

ACTIVE_DUMMY_CODES: tuple[str, ...] = tuple(
    item.promocode for item in DUMMY_PROMOCODES if item.note.startswith("ACTIVE")
)


def upsert_dummy(db, item: DummyPromocode, *, ttl_days: int, campaign_id) -> Promocode:
    existing = db.scalar(select(Promocode).where(Promocode.promocode == item.promocode))
    if existing is not None:
        if existing.campaign_id is None and campaign_id is not None:
            existing.campaign_id = campaign_id
            db.flush()
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
        campaign_id=campaign_id,
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
        campaign = upsert_campaign(
            db,
            code=DEMO_CAMPAIGN_CODE,
            name=DEMO_CAMPAIGN_NAME,
            starts_at=datetime.now(UTC),
            ends_at=None,
            notes="Dummy codes for cashier tryouts",
        )
        for item in DUMMY_PROMOCODES:
            row = upsert_dummy(
                db,
                item,
                ttl_days=settings.promocode_ttl_days,
                campaign_id=campaign.id,
            )
            printed.append((item, row.promocode, row.status.value, row.customer_erp_id))
        db.commit()

    print("Dummy promocodes for testing:")
    print(f"Campaign: {DEMO_CAMPAIGN_CODE} ({DEMO_CAMPAIGN_NAME})")
    print(f"{'code':<10}\t{'status':<8}\t{'customer':<16}\tnote")
    for item, code, status, customer in printed:
        print(f"{code:<10}\t{status:<8}\t{customer:<16}\t{item.note}")
    print()
    first = ACTIVE_DUMMY_CODES[0]
    last = ACTIVE_DUMMY_CODES[-1]
    print(f"ACTIVE pool: {first}–{last} ({len(ACTIVE_DUMMY_CODES)} codes)")
    print("NOT_FOUND test: scan any other 8-digit code, e.g. 99999999")


if __name__ == "__main__":
    main()
