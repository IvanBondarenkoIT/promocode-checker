from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.integrations.erp.types import CoffeeSaleMatch


class ErpError(Exception):
    """ERP access failure (proxy, direct, or config)."""


class ErpAdapter(Protocol):
    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
        all_customers: bool = False,
        row_limit: int | None = None,
    ) -> list[CoffeeSaleMatch]:
        """Return coffee-beans sales for customers in [since, until].

        When ``all_customers`` is True, ignore customer filter (day digests).
        """
