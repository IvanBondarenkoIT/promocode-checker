"""SQL drafts for coffee-beans sale lookups.

Column aliases are fixed for row parsing. Exact Granit table/join names are a
best-effort draft and must be validated against live ERP (open Stage 4 question).
Discount column is intentionally not invented — match is by coffee group whitelist.
"""

from __future__ import annotations

from datetime import datetime

from app.integrations.erp.types import CoffeeSaleMatch


def parse_coffee_group_ids(raw: str) -> tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(int(p) for p in parts)


def build_coffee_sales_query(
    *,
    group_ids: tuple[int, ...],
    customer_erp_ids: list[str],
    since: datetime,
    until: datetime,
) -> tuple[str, list[object]]:
    """Build parameterized Firebird-style query returning expected aliases.

    Expected row keys (case-insensitive):
    CUSTOMER_ERP_ID, SOLD_AT, GROUP_ID, PRODUCT_NAME
    """
    if not group_ids:
        raise ValueError("coffee group_ids whitelist is empty")
    if not customer_erp_ids:
        return (
            """
SELECT CAST(NULL AS VARCHAR(64)) AS CUSTOMER_ERP_ID,
       CAST(NULL AS TIMESTAMP) AS SOLD_AT,
       CAST(NULL AS INTEGER) AS GROUP_ID,
       CAST(NULL AS VARCHAR(255)) AS PRODUCT_NAME
FROM RDB$DATABASE
WHERE 1 = 0
""".strip(),
            [],
        )

    group_placeholders = ", ".join("?" for _ in group_ids)
    customer_placeholders = ", ".join("?" for _ in customer_erp_ids)

    # Draft join shape aligned with Granit-style DOC/GOODS/GROUP tables.
    # Live ERP may require different table names — do not treat as final schema.
    query = f"""
SELECT
    CAST(c.ID AS VARCHAR(64)) AS CUSTOMER_ERP_ID,
    d.DOC_DATE AS SOLD_AT,
    g.GROUP_ID AS GROUP_ID,
    g.NAME AS PRODUCT_NAME
FROM DOCHEAD d
JOIN DOCLINE dl ON dl.DOC_ID = d.ID
JOIN GOODS g ON g.ID = dl.GOODS_ID
JOIN CLIENTS c ON c.ID = d.CLIENT_ID
WHERE g.GROUP_ID IN ({group_placeholders})
  AND CAST(c.ID AS VARCHAR(64)) IN ({customer_placeholders})
  AND d.DOC_DATE >= ?
  AND d.DOC_DATE <= ?
""".strip()

    params: list[object] = [
        *group_ids,
        *customer_erp_ids,
        since,
        until,
    ]
    return query, params


def rows_to_matches(rows: list[dict]) -> list[CoffeeSaleMatch]:
    matches: list[CoffeeSaleMatch] = []
    for row in rows:
        normalized = {str(k).upper(): v for k, v in row.items()}
        customer = normalized.get("CUSTOMER_ERP_ID")
        sold_at = normalized.get("SOLD_AT")
        group_id = normalized.get("GROUP_ID")
        if customer is None or sold_at is None or group_id is None:
            continue
        matches.append(
            CoffeeSaleMatch(
                customer_erp_id=str(customer),
                sold_at=sold_at,
                group_id=int(group_id),
                product_name=(
                    str(normalized["PRODUCT_NAME"])
                    if normalized.get("PRODUCT_NAME") is not None
                    else None
                ),
            )
        )
    return matches
