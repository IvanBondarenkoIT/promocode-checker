from __future__ import annotations

import logging
from datetime import datetime

from app.core.config import Settings, get_settings
from app.integrations.erp.base import ErpAdapter, ErpError
from app.integrations.erp.direct import DirectErpAdapter
from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.proxy import ProxyErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch

logger = logging.getLogger(__name__)


class FallbackErpAdapter:
    """Try primary adapter, then optional fallback on ErpError."""

    def __init__(self, primary: ErpAdapter, fallback: ErpAdapter | None) -> None:
        self._primary = primary
        self._fallback = fallback

    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
        all_customers: bool = False,
        row_limit: int | None = None,
    ) -> list[CoffeeSaleMatch]:
        try:
            return self._primary.find_coffee_sales(
                customer_erp_ids,
                since=since,
                until=until,
                all_customers=all_customers,
                row_limit=row_limit,
            )
        except ErpError as primary_error:
            if self._fallback is None:
                raise
            logger.warning("Primary ERP adapter failed, trying fallback: %s", primary_error)
            return self._fallback.find_coffee_sales(
                customer_erp_ids,
                since=since,
                until=until,
                all_customers=all_customers,
                row_limit=row_limit,
            )


def get_erp_adapter(
    settings: Settings | None = None,
    *,
    mock_sales: list[CoffeeSaleMatch] | None = None,
) -> ErpAdapter:
    cfg = settings or get_settings()
    mode = (cfg.erp_access_mode or "proxy").strip().lower()

    if mode == "mock":
        return MockErpAdapter(sales=mock_sales)

    if mode == "direct":
        return DirectErpAdapter(cfg)

    if mode == "proxy":
        primary = ProxyErpAdapter(cfg)
        fallback: ErpAdapter | None = None
        if (cfg.firebird_dsn or "").strip():
            try:
                fallback = DirectErpAdapter(cfg)
            except ErpError as exc:
                logger.warning("Direct ERP fallback unavailable: %s", exc)
        return FallbackErpAdapter(primary, fallback)

    raise ErpError(f"Unsupported ERP_ACCESS_MODE={cfg.erp_access_mode!r}")
