"""Evaluate coffee sales against the promo kg threshold (per order)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.integrations.erp.types import CoffeeSaleMatch


class SaleVerdict(StrEnum):
    QUALIFIED = "QUALIFIED"
    NOT_ENOUGH_KG = "NOT_ENOUGH_KG"
    UNKNOWN_WEIGHT = "UNKNOWN_WEIGHT"


@dataclass
class EvaluatedOrder:
    customer_erp_id: str
    order_id: str
    sold_at: datetime
    customer_name: str | None
    order_kg: float | None
    qty_pieces: float
    total_amount: float | None
    products: list[str] = field(default_factory=list)
    group_ids: list[int] = field(default_factory=list)
    verdict: SaleVerdict = SaleVerdict.NOT_ENOUGH_KG
    lines: list[CoffeeSaleMatch] = field(default_factory=list)


def evaluate_orders(
    sales: list[CoffeeSaleMatch],
    *,
    min_coffee_kg: float,
) -> list[EvaluatedOrder]:
    """Group sale lines by (customer, order_id) and classify against the kg threshold."""
    buckets: dict[tuple[str, str], list[CoffeeSaleMatch]] = {}
    for sale in sales:
        order_id = (sale.order_id or "").strip()
        if not order_id:
            # Synthetic key so orphan lines are still observable once.
            order_id = f"no-order:{sale.sold_at.isoformat()}:{sale.group_id}"
        key = (sale.customer_erp_id, order_id)
        buckets.setdefault(key, []).append(sale)

    results: list[EvaluatedOrder] = []
    for (customer_erp_id, order_id), lines in buckets.items():
        lines_sorted = sorted(lines, key=lambda row: row.sold_at)
        sold_at = lines_sorted[0].sold_at
        customer_name = next(
            (row.customer_name for row in lines_sorted if row.customer_name),
            None,
        )
        products: list[str] = []
        group_ids: list[int] = []
        # Sum of SOURCE values (already kg in live Granit); column name is historical.
        qty_pieces = 0.0
        amount = 0.0
        has_amount = False
        kg_sum = 0.0
        unknown = False

        for row in lines_sorted:
            qty = float(row.quantity or 0)
            qty_pieces += qty
            if row.unit_price is not None:
                amount += float(row.unit_price) * qty
                has_amount = True
            if row.product_name:
                products.append(row.product_name)
            group_ids.append(row.group_id)
            if row.line_kg is None:
                unknown = True
            else:
                kg_sum += float(row.line_kg)

        if unknown and kg_sum <= 0:
            verdict = SaleVerdict.UNKNOWN_WEIGHT
            order_kg: float | None = None
        elif unknown:
            # Partial weight: treat known kg only; still flag unknown if under threshold.
            order_kg = round(kg_sum, 4)
            if order_kg >= min_coffee_kg:
                verdict = SaleVerdict.QUALIFIED
            else:
                verdict = SaleVerdict.UNKNOWN_WEIGHT
        else:
            order_kg = round(kg_sum, 4)
            verdict = (
                SaleVerdict.QUALIFIED
                if order_kg >= min_coffee_kg
                else SaleVerdict.NOT_ENOUGH_KG
            )

        results.append(
            EvaluatedOrder(
                customer_erp_id=customer_erp_id,
                order_id=order_id,
                sold_at=sold_at,
                customer_name=customer_name,
                order_kg=order_kg,
                qty_pieces=round(qty_pieces, 4),
                total_amount=round(amount, 2) if has_amount else None,
                products=products,
                group_ids=sorted(set(group_ids)),
                verdict=verdict,
                lines=lines_sorted,
            )
        )

    results.sort(key=lambda item: item.sold_at)
    return results
