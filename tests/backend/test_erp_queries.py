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
    assert "I.SOURCE AS QUANTITY" in query
    assert "G.NW AS NET_WEIGHT_KG" in query
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
                "PRODUCT_NAME": "blend (250 g)",
                "CUSTOMER_NAME": "КЛИЕНТ PALIASHVILI",
                "ORDER_ID": "99",
                "QUANTITY": 2.0,
                "NET_WEIGHT_KG": 0.25,
                "UNIT_PRICE": 45,
            }
        ]
    )
    assert len(matches) == 1
    row = matches[0]
    assert row.customer_erp_id == "12523"
    assert row.order_id == "99"
    assert row.quantity == 2.0
    assert row.net_weight_kg == 0.25
    assert row.line_kg == 2.0


def test_rows_to_matches_parses_string_sold_at() -> None:
    matches = rows_to_matches(
        [
            {
                "CUSTOMER_ERP_ID": "12523",
                "SOLD_AT": "2026-08-04T00:00:00",
                "GROUP_ID": 11077,
                "PRODUCT_NAME": "blend",
            }
        ]
    )
    assert len(matches) == 1
    assert matches[0].sold_at == datetime(2026, 8, 4, 0, 0, 0)


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


def test_proxy_json_safe_params_strips_tz() -> None:
    from app.integrations.erp.proxy import _json_safe_params

    aware = datetime(2026, 8, 4, 0, 0, tzinfo=UTC)
    out = _json_safe_params([aware, "12523", 11077])
    assert out[0] == "2026-08-04 00:00:00"
    assert out[1:] == ["12523", 11077]
