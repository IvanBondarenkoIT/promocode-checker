from datetime import UTC, datetime, timedelta

from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch


def test_mock_filters_by_customer_and_window() -> None:
    now = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    sales = [
        CoffeeSaleMatch("C1", now - timedelta(hours=1), 11077, "blend"),
        CoffeeSaleMatch("C1", now - timedelta(hours=5), 11077, "old"),
        CoffeeSaleMatch("C2", now - timedelta(minutes=30), 16276, "other"),
    ]
    adapter = MockErpAdapter(sales)

    found = adapter.find_coffee_sales(
        ["C1"],
        since=now - timedelta(hours=2),
        until=now,
    )

    assert len(found) == 1
    assert found[0].product_name == "blend"


def test_mock_empty_customers_returns_empty() -> None:
    adapter = MockErpAdapter(
        [CoffeeSaleMatch("C1", datetime(2026, 7, 28, tzinfo=UTC), 11077)]
    )
    found = adapter.find_coffee_sales(
        [],
        since=datetime(2026, 1, 1, tzinfo=UTC),
        until=datetime(2026, 12, 1, tzinfo=UTC),
    )
    assert found == []
