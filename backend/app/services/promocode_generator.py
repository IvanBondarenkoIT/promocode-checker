import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Promocode, PromocodeStatus

PROMOCODE_LENGTH = 8
PROMOCODE_DIGITS = string.digits
MAX_GENERATION_ATTEMPTS = 100


def is_valid_promocode(value: str) -> bool:
    return len(value) == PROMOCODE_LENGTH and value.isdigit()


def calculate_expires_at(created_at: datetime, ttl_days: int) -> datetime:
    return created_at + timedelta(days=ttl_days)


def generate_unique_promocode(db: Session, *, max_attempts: int = MAX_GENERATION_ATTEMPTS) -> str:
    for _ in range(max_attempts):
        candidate = "".join(secrets.choice(PROMOCODE_DIGITS) for _ in range(PROMOCODE_LENGTH))
        exists = db.scalar(select(Promocode.id).where(Promocode.promocode == candidate))
        if exists is None:
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
