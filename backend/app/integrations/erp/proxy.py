"""Proxy API ERP client (primary Granit access path)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.integrations.erp.base import ErpError
from app.integrations.erp.queries import (
    build_coffee_sales_query,
    parse_coffee_group_ids,
    parse_paid_statuses,
    rows_to_matches,
)
from app.integrations.erp.types import CoffeeSaleMatch

logger = logging.getLogger(__name__)


class ProxyErpAdapter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = (settings.proxy_api_url or "").rstrip("/")
        self._token = settings.proxy_api_token or ""
        self._timeout = settings.proxy_api_timeout
        self._max_retries = max(1, settings.proxy_api_max_retries)
        self._group_ids = parse_coffee_group_ids(settings.coffee_beans_group_ids)
        self._paid_statuses = parse_paid_statuses(settings.erp_paid_statuses)

    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
        all_customers: bool = False,
        row_limit: int | None = None,
    ) -> list[CoffeeSaleMatch]:
        if not self._base_url:
            raise ErpError("PROXY_API_URL is not set")
        if not self._token:
            raise ErpError("PROXY_API_TOKEN is not set")

        query, params = build_coffee_sales_query(
            group_ids=self._group_ids,
            customer_erp_ids=customer_erp_ids,
            since=since,
            until=until,
            paid_statuses=self._paid_statuses,
            all_customers=all_customers,
            row_limit=row_limit,
        )
        rows = self._execute_query(query, params)
        return rows_to_matches(rows)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _execute_query(self, query: str, params: list[object]) -> list[dict[str, Any]]:
        url = f"{self._base_url}/api/query"
        payload = {"query": query, "params": _json_safe_params(params)}
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, json=payload, headers=self._headers())
                data = response.json() if response.content else {}
                if not response.is_success:
                    raise ErpError(
                        f"Proxy query failed ({response.status_code}): "
                        f"{data.get('error', response.text)}"
                    )
                if not data.get("success", True) and "data" not in data:
                    raise ErpError(f"Proxy query unsuccessful: {data.get('error', data)}")
                rows = data.get("data")
                if rows is None:
                    rows = data.get("rows") or []
                if not isinstance(rows, list):
                    raise ErpError("Proxy query response data is not a list")
                return rows
            except ErpError:
                raise
            except Exception as exc:  # noqa: BLE001 — retry network/parse failures
                last_error = exc
                logger.warning(
                    "Proxy ERP attempt %s/%s failed: %s",
                    attempt,
                    self._max_retries,
                    exc,
                )

        raise ErpError(f"Proxy query failed after retries: {last_error}") from last_error


def _json_safe_params(params: list[object]) -> list[object]:
    """Serialize params for Proxy API JSON body.

    Firebird via fdb rejects / mis-compares ISO timestamps with offsets
    (e.g. ``2026-08-04T00:00:00+04:00``). Send naive ``YYYY-MM-DD HH:MM:SS``.
    """
    out: list[object] = []
    for value in params:
        if isinstance(value, datetime):
            naive = value.replace(tzinfo=None) if value.tzinfo is not None else value
            out.append(naive.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            out.append(value)
    return out
