"""Direct read-only Firebird ERP access (fallback)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import Settings
from app.integrations.erp.base import ErpError
from app.integrations.erp.queries import (
    build_coffee_sales_query,
    parse_coffee_group_ids,
    rows_to_matches,
)
from app.integrations.erp.types import CoffeeSaleMatch


class DirectErpAdapter:
    def __init__(self, settings: Settings) -> None:
        self._dsn = (settings.firebird_dsn or "").strip()
        self._user = (settings.firebird_user or "").strip()
        self._password = (settings.firebird_password or "").strip()
        self._group_ids = parse_coffee_group_ids(settings.coffee_beans_group_ids)

        if not self._dsn:
            raise ErpError("FIREBIRD_DSN is not set (direct mode)")
        if not self._user:
            raise ErpError("FIREBIRD_USER is not set (direct mode)")
        if not self._password:
            raise ErpError("FIREBIRD_PASSWORD is not set (direct mode)")

    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
    ) -> list[CoffeeSaleMatch]:
        query, params = build_coffee_sales_query(
            group_ids=self._group_ids,
            customer_erp_ids=customer_erp_ids,
            since=since,
            until=until,
        )
        rows = self._execute_query(query, params)
        return rows_to_matches(rows)

    def _execute_query(self, query: str, params: list[object]) -> list[dict[str, Any]]:
        try:
            import fdb  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ErpError(
                "fdb package is required for ERP_ACCESS_MODE=direct; "
                "install firebird driver or use proxy/mock"
            ) from exc

        try:
            conn = fdb.connect(
                dsn=self._dsn,
                user=self._user,
                password=self._password,
                charset="UTF8",
            )
        except Exception as exc:  # noqa: BLE001
            raise ErpError(f"Firebird connect failed: {exc}") from exc

        try:
            cur = conn.cursor()
            try:
                cur.execute(query, tuple(params) if params else ())
                cols = [d[0] for d in (cur.description or [])]
                rows = cur.fetchall()
                return [{cols[i]: row[i] for i in range(len(cols))} for row in rows]
            finally:
                cur.close()
        except ErpError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ErpError(f"Firebird query failed: {exc}") from exc
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
