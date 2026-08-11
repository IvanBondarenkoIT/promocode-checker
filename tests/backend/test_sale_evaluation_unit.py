from datetime import UTC, datetime

from app.integrations.erp.types import CoffeeSaleMatch
from app.services.coffee_weight import infer_net_weight_kg, line_kg, resolve_net_weight_kg
from app.services.sale_evaluation import SaleVerdict, evaluate_orders


def test_infer_net_weight_from_name() -> None:
    assert infer_net_weight_kg('Coffee "Blaser" (250 g)') == 0.25
    assert infer_net_weight_kg("Blend 1kg") == 1.0
    assert infer_net_weight_kg("no weight") is None


def test_resolve_prefers_stored_then_name_then_group() -> None:
    assert resolve_net_weight_kg(stored_nw=0.25) == 0.25
    assert resolve_net_weight_kg(product_name="Pack 1 kg") == 1.0
    assert resolve_net_weight_kg(group_id=16279) == 1.0
    assert resolve_net_weight_kg(group_id=99999) is None


def test_line_kg_pieces_times_weight() -> None:
    assert line_kg(8, stored_nw=0.25) == 2.0
    assert line_kg(2, group_id=16279) == 2.0
    assert line_kg(1, product_name="mystery") is None


def test_evaluate_order_qualified_at_two_kg() -> None:
    sold = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    sales = [
        CoffeeSaleMatch(
            customer_erp_id="1",
            sold_at=sold,
            group_id=11077,
            product_name="250 g",
            order_id="o1",
            quantity=8,
            net_weight_kg=0.25,
            line_kg=2.0,
        )
    ]
    orders = evaluate_orders(sales, min_coffee_kg=2.0)
    assert len(orders) == 1
    assert orders[0].verdict == SaleVerdict.QUALIFIED
    assert orders[0].order_kg == 2.0


def test_evaluate_order_not_enough() -> None:
    sold = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    sales = [
        CoffeeSaleMatch(
            customer_erp_id="1",
            sold_at=sold,
            group_id=11077,
            product_name="250 g",
            order_id="o1",
            quantity=4,
            net_weight_kg=0.25,
            line_kg=1.0,
        )
    ]
    orders = evaluate_orders(sales, min_coffee_kg=2.0)
    assert orders[0].verdict == SaleVerdict.NOT_ENOUGH_KG
    assert orders[0].order_kg == 1.0


def test_evaluate_aggregates_lines_in_same_order() -> None:
    sold = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    sales = [
        CoffeeSaleMatch(
            customer_erp_id="1",
            sold_at=sold,
            group_id=11077,
            product_name="250 g",
            order_id="o1",
            quantity=4,
            net_weight_kg=0.25,
            line_kg=1.0,
        ),
        CoffeeSaleMatch(
            customer_erp_id="1",
            sold_at=sold,
            group_id=16279,
            product_name="1kg",
            order_id="o1",
            quantity=1,
            net_weight_kg=1.0,
            line_kg=1.0,
        ),
    ]
    orders = evaluate_orders(sales, min_coffee_kg=2.0)
    assert len(orders) == 1
    assert orders[0].verdict == SaleVerdict.QUALIFIED
    assert orders[0].order_kg == 2.0
