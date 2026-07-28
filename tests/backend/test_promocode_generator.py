from datetime import UTC, datetime

import pytest
from app.core.config import Settings
from app.models import PromocodeStatus
from app.services.promocode_generator import (
    bulk_create_promocodes,
    create_promocode_for_customer,
    is_valid_promocode,
)

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def test_create_promocode_for_customer_persists_active_code(
    db_session,
    test_settings: Settings,
) -> None:
    promocode = create_promocode_for_customer(
        db_session,
        customer_erp_id="CUST-1001",
        settings=test_settings,
        created_at=datetime(2026, 7, 28, 12, 0, tzinfo=UTC),
    )
    db_session.commit()

    assert promocode.status == PromocodeStatus.ACTIVE
    assert promocode.customer_erp_id == "CUST-1001"
    assert is_valid_promocode(promocode.promocode)
    assert promocode.expires_at == datetime(2026, 8, 27, 12, 0, tzinfo=UTC)


def test_bulk_create_promocodes_generates_unique_codes(db_session, test_settings: Settings) -> None:
    promocodes = bulk_create_promocodes(
        db_session,
        customer_erp_ids=["CUST-1", "CUST-2", "CUST-3"],
        settings=test_settings,
    )
    db_session.commit()

    codes = {item.promocode for item in promocodes}
    assert len(codes) == 3
    assert all(is_valid_promocode(code) for code in codes)
