from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CoffeeSaleMatch:
    customer_erp_id: str
    sold_at: datetime
    group_id: int
    product_name: str | None = None
    customer_name: str | None = None
    order_id: str | None = None
    unit_price: float | None = None
