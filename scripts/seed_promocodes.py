"""Seed a few ACTIVE promocodes for local cashier testing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.promocode_generator import create_promocode_for_customer  # noqa: E402

DEFAULT_CUSTOMERS = ["CUST-SEED-1", "CUST-SEED-2", "CUST-SEED-3"]


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        created = [
            create_promocode_for_customer(
                db,
                customer_erp_id=customer_erp_id,
                settings=settings,
            )
            for customer_erp_id in DEFAULT_CUSTOMERS
        ]
        db.commit()
        for item in created:
            print(f"{item.customer_erp_id}\t{item.promocode}\t{item.status.value}")


if __name__ == "__main__":
    main()
