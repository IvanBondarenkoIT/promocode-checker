import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Promocode, PromocodeStatus

PROMOCODE_MIN_LENGTH = 8
PROMOCODE_MAX_LENGTH = 20
PROMOCODE_LENGTH = 8  # length used by the random generator (demo / tests)
PROMOCODE_DIGITS = string.digits
MAX_GENERATION_ATTEMPTS = 100


def is_valid_promocode(value: str) -> bool:
    return value.isdigit() and PROMOCODE_MIN_LENGTH <= len(value) <= PROMOCODE_MAX_LENGTH


def promocode_format_hint() -> str:
    return f"{PROMOCODE_MIN_LENGTH}-{PROMOCODE_MAX_LENGTH} digits"


def calculate_expires_at(created_at: datetime, ttl_days: int) -> datetime:
    return created_at + timedelta(days=ttl_days)


def generate_unique_promocode(
    db: Session,
    *,
    max_attempts: int = MAX_GENERATION_ATTEMPTS,
    prefix: str | None = None,
    reserved: set[str] | None = None,
) -> str:
    """Random 8-digit code unique across the whole table.

    ``prefix`` pins the leading digits so campaigns never share a range.
    ``reserved`` holds codes generated in the same uncommitted batch.
    """
    lead = (prefix or "").strip()
    if lead and (not lead.isdigit() or len(lead) >= PROMOCODE_LENGTH):
        raise ValueError(f"Invalid promocode prefix: {prefix!r}")

    random_len = PROMOCODE_LENGTH - len(lead)
    for _ in range(max_attempts):
        candidate = lead + "".join(secrets.choice(PROMOCODE_DIGITS) for _ in range(random_len))
        if reserved is not None and candidate in reserved:
            continue
        exists = db.scalar(select(Promocode.id).where(Promocode.promocode == candidate))
        if exists is None:
            if reserved is not None:
                reserved.add(candidate)
            return candidate
    raise RuntimeError("Failed to generate a unique promocode after multiple attempts")


def create_promocode_for_customer(
    db: Session,
    *,
    customer_erp_id: str,
    settings: Settings,
    created_at: datetime | None = None,
) -> Promocode:
    created = created_at or datetime.now(UTC)
    promocode = Promocode(
        customer_erp_id=customer_erp_id,
        promocode=generate_unique_promocode(db),
        status=PromocodeStatus.ACTIVE,
        created_at=created,
        expires_at=calculate_expires_at(created, settings.promocode_ttl_days),
    )
    db.add(promocode)
    db.flush()
    return promocode


def bulk_create_promocodes(
    db: Session,
    *,
    customer_erp_ids: list[str],
    settings: Settings,
) -> list[Promocode]:
    created: list[Promocode] = []
    for customer_erp_id in customer_erp_ids:
        created.append(
            create_promocode_for_customer(
                db,
                customer_erp_id=customer_erp_id,
                settings=settings,
            )
        )
    return created
