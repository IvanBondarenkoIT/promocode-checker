from __future__ import annotations

from datetime import UTC, datetime

from app.integrations.erp.types import CoffeeSaleMatch


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class MockErpAdapter:
    """In-memory ERP sales for local tests and offline reconcile."""

    def __init__(self, sales: list[CoffeeSaleMatch] | None = None) -> None:
        self.sales = list(sales or [])

    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
    ) -> list[CoffeeSaleMatch]:
        wanted = set(customer_erp_ids)
        since_aware = _ensure_aware(since)
        until_aware = _ensure_aware(until)
        return [
            sale
            for sale in self.sales
            if sale.customer_erp_id in wanted
            and since_aware <= _ensure_aware(sale.sold_at) <= until_aware
        ]
