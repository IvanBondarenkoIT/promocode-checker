from datetime import UTC, datetime, timedelta

from app.integrations.erp.queries import (
    build_coffee_sales_query,
    parse_coffee_group_ids,
    parse_paid_statuses,
    rows_to_matches,
)
from app.integrations.erp.types import CoffeeSaleMatch


def test_parse_helpers() -> None:
    assert parse_coffee_group_ids("11077, 16276") == (11077, 16276)
    assert parse_paid_statuses("1,2,3,5") == ("1", "2", "3", "5")
    assert parse_paid_statuses("") == ("1", "2", "3", "5")


def test_build_query_uses_granit_tables() -> None:
    since = datetime(2026, 8, 4, 0, 0, tzinfo=UTC)
    until = datetime(2026, 8, 4, 23, 59, tzinfo=UTC)
    query, params = build_coffee_sales_query(
        group_ids=(11077, 16276),
        customer_erp_ids=["12523", "21470"],
        since=since,
        until=until,
        paid_statuses=("1", "2", "3", "5"),
    )
    assert "STORZAKAZDT" in query
    assert "STORZDTGDS" in query
    assert "GOODS" in query
    assert "ORGN" in query
    assert "DOCHEAD" not in query
    assert "G.OWNER" in query
    assert params[:2] == [11077, 16276]
    assert params[2:4] == ["12523", "21470"]
    assert params[4:8] == ["1", "2", "3", "5"]
    assert params[-2:] == [since, until]


def test_build_query_empty_customers() -> None:
    query, params = build_coffee_sales_query(
        group_ids=(11077,),
        customer_erp_ids=[],
        since=datetime(2026, 1, 1, tzinfo=UTC),
        until=datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert "WHERE 1 = 0" in query
    assert params == []


def test_build_query_all_customers_with_limit() -> None:
    since = datetime(2026, 8, 4, 0, 0, tzinfo=UTC)
    until = datetime(2026, 8, 4, 23, 59, tzinfo=UTC)
    query, params = build_coffee_sales_query(
        group_ids=(11077,),
        customer_erp_ids=[],
        since=since,
        until=until,
        paid_statuses=("1",),
        all_customers=True,
        row_limit=100,
    )
    assert "FIRST 100" in query
    assert "CAST(S.ORGNID AS VARCHAR(64)) IN" not in query
    assert params == [11077, "1", since, until]


def test_rows_to_matches_optional_fields() -> None:
    sold = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    matches = rows_to_matches(
        [
            {
                "CUSTOMER_ERP_ID": "12523",
                "SOLD_AT": sold,
                "GROUP_ID": 11077,
                "PRODUCT_NAME": "blend",
                "CUSTOMER_NAME": "КЛИЕНТ PALIASHVILI",
                "ORDER_ID": "99",
            }
        ]
    )
    assert len(matches) == 1
    assert matches[0] == CoffeeSaleMatch(
        customer_erp_id="12523",
        sold_at=sold,
        group_id=11077,
        product_name="blend",
        customer_name="КЛИЕНТ PALIASHVILI",
        order_id="99",
    )


def test_mock_still_filters() -> None:
    from app.integrations.erp.mock import MockErpAdapter

    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    adapter = MockErpAdapter(
        [
            CoffeeSaleMatch("12523", now - timedelta(hours=1), 11077, "ok"),
            CoffeeSaleMatch("12523", now - timedelta(hours=5), 11077, "old"),
        ]
    )
    found = adapter.find_coffee_sales(
        ["12523"],
        since=now - timedelta(hours=2),
        until=now,
    )
    assert len(found) == 1
    assert found[0].product_name == "ok"
