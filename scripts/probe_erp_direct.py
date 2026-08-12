"""Probe direct Firebird ERP connectivity and coffee sales (read-only).

Examples:
  python scripts/probe_erp_direct.py --days 7
  python scripts/probe_erp_direct.py --customer-ids 21470,12523 --days 30
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.integrations.erp.base import ErpError  # noqa: E402
from app.integrations.erp.direct import DirectErpAdapter  # noqa: E402
from app.integrations.erp.factory import get_erp_adapter  # noqa: E402


def _load_customer_ids_from_db() -> list[str]:
    from app.db.session import SessionLocal  # noqa: E402
    from app.models import Campaign, Promocode, PromocodeStatus  # noqa: E402
    from app.services.campaign_scope import get_active_kind  # noqa: E402
    from sqlalchemy import select

    with SessionLocal() as db:
        active_kind = get_active_kind(db)
        rows = db.scalars(
            select(Promocode.customer_erp_id)
            .join(Campaign, Campaign.id == Promocode.campaign_id)
            .where(
                Promocode.status == PromocodeStatus.ACTIVE,
                Campaign.kind == active_kind,
            )
            .distinct()
        ).all()
    return sorted({str(row).strip() for row in rows if row})


def _print_config(settings) -> None:
    mode = (settings.erp_access_mode or "").strip().lower()
    print(f"ERP_ACCESS_MODE={mode}")
    print(f"FIREBIRD_DSN={settings.firebird_dsn or '(empty)'}")
    print(f"FIREBIRD_USER={settings.firebird_user or '(empty)'}")
    lib = settings.firebird_library_path or "(system default)"
    print(f"FIREBIRD_LIBRARY_PATH={lib}")
    print(f"COFFEE_BEANS_GROUP_IDS={settings.coffee_beans_group_ids}")


def _print_sales_table(sales) -> None:
    if not sales:
        print("No coffee sales in window.")
        return
    by_order: dict[str, list] = {}
    for sale in sales:
        key = f"{sale.customer_erp_id}:{sale.order_id or '?'}"
        by_order.setdefault(key, []).append(sale)

    print(f"Sales lines: {len(sales)}  unique orders: {len(by_order)}")
    print("customer_erp_id | order_id | sold_at | order_kg | products")
    print("-" * 72)
    for key in sorted(by_order.keys()):
        lines = by_order[key]
        first = lines[0]
        order_kg = sum(line.line_kg or 0.0 for line in lines)
        products = ", ".join(line.product_name or "?" for line in lines[:3])
        sold = first.sold_at.isoformat() if first.sold_at else "?"
        print(
            f"{first.customer_erp_id} | {first.order_id or '?'} | {sold} | "
            f"{order_kg:.3f} | {products}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe direct Firebird ERP coffee sales.")
    parser.add_argument(
        "--customer-ids",
        default="",
        help="Comma-separated ORGN ids (default: ACTIVE promocodes in active campaign kind)",
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument(
        "--use-factory",
        action="store_true",
        help="Use get_erp_adapter() instead of DirectErpAdapter only",
    )
    args = parser.parse_args()

    settings = get_settings()
    _print_config(settings)

    if args.customer_ids.strip():
        customer_ids = [part.strip() for part in args.customer_ids.split(",") if part.strip()]
    else:
        try:
            customer_ids = _load_customer_ids_from_db()
        except Exception as exc:  # noqa: BLE001
            print(f"Could not load customer ids from DB: {exc}", file=sys.stderr)
            return 1
        if not customer_ids:
            print("No ACTIVE promocodes found for active campaign kind.", file=sys.stderr)
            return 1

    print(f"Customers: {len(customer_ids)} (showing up to 10): {', '.join(customer_ids[:10])}")

    until = datetime.now(UTC)
    since = until - timedelta(days=max(1, args.days))

    try:
        if args.use_factory:
            adapter = get_erp_adapter(settings)
            print(f"Adapter: {type(adapter).__name__}")
            if isinstance(adapter, DirectErpAdapter):
                print(f"Engine version: {adapter.server_version()}")
            sales = adapter.find_coffee_sales(customer_ids, since=since, until=until)
        else:
            direct = DirectErpAdapter(settings)
            print(f"Engine version: {direct.server_version()}")
            sales = direct.find_coffee_sales(customer_ids, since=since, until=until)
    except ErpError as exc:
        print(f"ERP probe failed: {exc}", file=sys.stderr)
        return 1

    _print_sales_table(sales)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
