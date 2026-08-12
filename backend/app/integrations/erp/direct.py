"""Direct read-only Firebird ERP access."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import Settings
from app.integrations.erp.base import ErpError
from app.integrations.erp.queries import (
    build_coffee_sales_query,
    parse_coffee_group_ids,
    parse_paid_statuses,
    rows_to_matches,
)
from app.integrations.erp.types import CoffeeSaleMatch

_ENGINE_VERSION_SQL = (
    "SELECT rdb$get_context('SYSTEM', 'ENGINE_VERSION') FROM RDB$DATABASE"
)


class DirectErpAdapter:
    def __init__(self, settings: Settings) -> None:
        self._dsn = (settings.firebird_dsn or "").strip()
        self._user = (settings.firebird_user or "").strip()
        self._password = (settings.firebird_password or "").strip()
        self._library_path = (settings.firebird_library_path or "").strip()
        self._group_ids = parse_coffee_group_ids(settings.coffee_beans_group_ids)
        self._paid_statuses = parse_paid_statuses(settings.erp_paid_statuses)

        if not self._dsn:
            raise ErpError("FIREBIRD_DSN is not set (direct mode)")
        if not self._user:
            raise ErpError("FIREBIRD_USER is not set (direct mode)")
        if not self._password:
            raise ErpError("FIREBIRD_PASSWORD is not set (direct mode)")

    @property
    def dsn(self) -> str:
        return self._dsn

    @property
    def user(self) -> str:
        return self._user

    @property
    def library_path(self) -> str:
        return self._library_path

    def _connect_context(self) -> str:
        lib = f", library={self._library_path}" if self._library_path else ""
        return f"dsn={self._dsn}, user={self._user}{lib}"

    def find_coffee_sales(
        self,
        customer_erp_ids: list[str],
        *,
        since: datetime,
        until: datetime,
        all_customers: bool = False,
        row_limit: int | None = None,
    ) -> list[CoffeeSaleMatch]:
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

    def server_version(self) -> str:
        rows = self._execute_query(_ENGINE_VERSION_SQL, [])
        if not rows:
            return "unknown"
        first = rows[0]
        value = next(iter(first.values()), None)
        return str(value).strip() if value is not None else "unknown"

    def _execute_query(self, query: str, params: list[object]) -> list[dict[str, Any]]:
        try:
            import fdb  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ErpError(
                "fdb package is required for ERP_ACCESS_MODE=direct; "
                "install firebird driver or use proxy/mock"
            ) from exc

        connect_kwargs: dict[str, object] = {
            "dsn": self._dsn,
            "user": self._user,
            "password": self._password,
            "charset": "UTF8",
        }
        if self._library_path:
            connect_kwargs["fb_library_name"] = self._library_path

        try:
            conn = fdb.connect(**connect_kwargs)
        except Exception as exc:  # noqa: BLE001
            raise ErpError(
                f"Firebird connect failed ({self._connect_context()}): {exc}"
            ) from exc

        try:
            cur = conn.cursor()
            try:
                fb_params = tuple(_firebird_params(params)) if params else ()
                cur.execute(query, fb_params)
                cols = [d[0] for d in (cur.description or [])]
                rows = cur.fetchall()
                return [{cols[i]: row[i] for i in range(len(cols))} for row in rows]
            finally:
                cur.close()
        except ErpError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ErpError(
                f"Firebird query failed ({self._connect_context()}): {exc}"
            ) from exc
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass


def _firebird_params(params: list[object]) -> list[object]:
    """Strip tzinfo so Firebird timestamp compare matches DAT_."""
    out: list[object] = []
    for value in params:
        if isinstance(value, datetime) and value.tzinfo is not None:
            out.append(value.replace(tzinfo=None))
        else:
            out.append(value)
    return out
