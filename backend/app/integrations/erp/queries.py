"""SQL for coffee-beans sale lookups against live Granit (Firebird).

Schema aligned with granit-clients-based-segmentation:
ORGN + STORZAKAZDT + STORZDTGDS + GOODS (OWNER = product group).

Discount column is intentionally not used — match is by coffee group whitelist.
"""

from __future__ import annotations

from datetime import datetime

from app.integrations.erp.types import CoffeeSaleMatch


def parse_coffee_group_ids(raw: str) -> tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(int(p) for p in parts)


def parse_paid_statuses(raw: str) -> tuple[str, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(parts) if parts else ("1", "2", "3", "5")


def build_coffee_sales_query(
    *,
    group_ids: tuple[int, ...],
    customer_erp_ids: list[str],
    since: datetime,
    until: datetime,
    paid_statuses: tuple[str, ...] = ("1", "2", "3", "5"),
    all_customers: bool = False,
    row_limit: int | None = None,
) -> tuple[str, list[object]]:
    """Build parameterized Firebird-style query returning expected aliases.

    Expected row keys (case-insensitive):
    CUSTOMER_ERP_ID, SOLD_AT, GROUP_ID, PRODUCT_NAME,
    optional CUSTOMER_NAME, ORDER_ID

    When ``all_customers`` is True, skip ORGNID filter (probe only).
    Always pass ``row_limit`` for that mode (safety cap).
    """
    if not group_ids:
        raise ValueError("coffee group_ids whitelist is empty")
    if not paid_statuses:
        raise ValueError("paid_statuses whitelist is empty")
    if not all_customers and not customer_erp_ids:
        return (
            """
SELECT CAST(NULL AS VARCHAR(64)) AS CUSTOMER_ERP_ID,
       CAST(NULL AS TIMESTAMP) AS SOLD_AT,
       CAST(NULL AS INTEGER) AS GROUP_ID,
       CAST(NULL AS VARCHAR(255)) AS PRODUCT_NAME,
       CAST(NULL AS VARCHAR(255)) AS CUSTOMER_NAME,
       CAST(NULL AS VARCHAR(64)) AS ORDER_ID
FROM RDB$DATABASE
WHERE 1 = 0
""".strip(),
            [],
        )

    group_placeholders = ", ".join("?" for _ in group_ids)
    status_placeholders = ", ".join("?" for _ in paid_statuses)
    first_clause = f"FIRST {int(row_limit)} " if row_limit and row_limit > 0 else ""

    customer_clause = ""
    customer_params: list[object] = []
    if not all_customers:
        customer_placeholders = ", ".join("?" for _ in customer_erp_ids)
        customer_clause = f"AND CAST(S.ORGNID AS VARCHAR(64)) IN ({customer_placeholders})"
        customer_params = list(customer_erp_ids)

    query = f"""
SELECT {first_clause}
    CAST(S.ORGNID AS VARCHAR(64)) AS CUSTOMER_ERP_ID,
    S.DAT_ AS SOLD_AT,
    G.OWNER AS GROUP_ID,
    G.NAME AS PRODUCT_NAME,
    COALESCE(NULLIF(TRIM(O.FULLNAME), ''), O.NAME) AS CUSTOMER_NAME,
    CAST(S.ID AS VARCHAR(64)) AS ORDER_ID
FROM STORZAKAZDT S
JOIN STORZDTGDS I ON I.SZID = S.ID
JOIN GOODS G ON G.ID = I.GODSID
LEFT JOIN ORGN O ON O.ID = S.ORGNID
WHERE G.OWNER IN ({group_placeholders})
  {customer_clause}
  AND CAST(S.CSDTKTHBID AS VARCHAR(32)) IN ({status_placeholders})
  AND S.DAT_ >= ?
  AND S.DAT_ <= ?
""".strip()

    params: list[object] = [
        *group_ids,
        *customer_params,
        *paid_statuses,
        since,
        until,
    ]
    return query, params


def rows_to_matches(rows: list[dict]) -> list[CoffeeSaleMatch]:
    matches: list[CoffeeSaleMatch] = []
    for row in rows:
        normalized = {str(k).upper(): v for k, v in row.items()}
        customer = normalized.get("CUSTOMER_ERP_ID")
        sold_at = _parse_sold_at(normalized.get("SOLD_AT"))
        group_id = normalized.get("GROUP_ID")
        if customer is None or sold_at is None or group_id is None:
            continue
        product = normalized.get("PRODUCT_NAME")
        customer_name = normalized.get("CUSTOMER_NAME")
        order_id = normalized.get("ORDER_ID")
        matches.append(
            CoffeeSaleMatch(
                customer_erp_id=str(customer),
                sold_at=sold_at,
                group_id=int(group_id),
                product_name=str(product) if product is not None else None,
                customer_name=str(customer_name) if customer_name is not None else None,
                order_id=str(order_id) if order_id is not None else None,
            )
        )
    return matches


def _parse_sold_at(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    # Proxy often returns ``2026-08-04T00:00:00`` (naive) or with offset.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None
