"""Probe ERP for coffee-bean sales (visual CSV/JSON for Stage 4.1).

Examples:
  python scripts/probe_erp_coffee_sales.py --mode mock
  python scripts/probe_erp_coffee_sales.py --day today --customers config/test_shop_cards.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.integrations.erp.factory import get_erp_adapter  # noqa: E402
from app.integrations.erp.queries import (  # noqa: E402
    build_coffee_sales_query,
    parse_coffee_group_ids,
    parse_paid_statuses,
    rows_to_matches,
)
from app.integrations.erp.types import CoffeeSaleMatch  # noqa: E402

DEFAULT_ALL_COFFEE_LIMIT = 500


def load_shop_cards(path: Path) -> list[dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cards = raw.get("cards") if isinstance(raw, dict) else raw
    if not isinstance(cards, list) or not cards:
        raise SystemExit(f"No cards found in {path}")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in cards:
        cid = str(item.get("id", "")).strip()
        name = str(item.get("name", "")).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        out.append({"id": cid, "name": name or cid})
    return out


def resolve_day(day_arg: str, tz_name: str) -> date:
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    if day_arg.strip().lower() in {"today", ""}:
        return today
    return date.fromisoformat(day_arg.strip())


def day_window(day: date, tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = datetime.combine(day, time.max, tzinfo=tz)
    return start, end


def mock_sales_for_day(day: date, cards: list[dict[str, str]]) -> list[CoffeeSaleMatch]:
    tz = ZoneInfo("Asia/Tbilisi")
    base = datetime.combine(day, time(11, 30), tzinfo=tz)
    sales: list[CoffeeSaleMatch] = []
    groups = (11077, 16276, 16279)
    for index, card in enumerate(cards[:5]):
        sales.append(
            CoffeeSaleMatch(
                customer_erp_id=card["id"],
                sold_at=base + timedelta(minutes=index * 15),
                group_id=groups[index % len(groups)],
                product_name=f"Mock coffee for {card['name']}",
                customer_name=card["name"],
                order_id=f"MOCK-{card['id']}",
            )
        )
    return sales


def write_outputs(
    *,
    out_dir: Path,
    day: date,
    matches: list[CoffeeSaleMatch],
    name_by_id: dict[str, str],
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = day.isoformat()
    csv_path = out_dir / f"coffee_sales_{stamp}.csv"
    json_path = out_dir / f"coffee_sales_{stamp}.json"

    rows: list[dict[str, object]] = []
    for match in matches:
        sold = match.sold_at
        sold_s = sold.isoformat() if isinstance(sold, datetime) else str(sold)
        rows.append(
            {
                "customer_erp_id": match.customer_erp_id,
                "customer_name": match.customer_name
                or name_by_id.get(match.customer_erp_id, ""),
                "sold_at": sold_s,
                "group_id": match.group_id,
                "product_name": match.product_name or "",
                "order_id": match.order_id or "",
            }
        )

    fieldnames = [
        "customer_erp_id",
        "customer_name",
        "sold_at",
        "group_id",
        "product_name",
        "order_id",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(
            {"day": stamp, "count": len(rows), "rows": rows},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return csv_path, json_path


def print_summary(matches: list[CoffeeSaleMatch], name_by_id: dict[str, str]) -> None:
    counts = Counter(m.customer_erp_id for m in matches)
    print(f"Total coffee sale lines: {len(matches)}")
    print("Per shop card:")
    for cid, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        label = name_by_id.get(cid, "")
        print(f"  {cid}\t{count}\t{label}")
    if name_by_id:
        missing = [cid for cid in name_by_id if cid not in counts]
        if missing:
            print(f"No coffee lines today for {len(missing)} card(s): {', '.join(missing)}")


def enrich_names(
    matches: list[CoffeeSaleMatch], name_by_id: dict[str, str]
) -> list[CoffeeSaleMatch]:
    enriched: list[CoffeeSaleMatch] = []
    for match in matches:
        if match.customer_name:
            enriched.append(match)
            continue
        enriched.append(
            CoffeeSaleMatch(
                customer_erp_id=match.customer_erp_id,
                sold_at=match.sold_at,
                group_id=match.group_id,
                product_name=match.product_name,
                customer_name=name_by_id.get(match.customer_erp_id),
                order_id=match.order_id,
            )
        )
    return enriched


def fetch_all_coffee(
    settings, since: datetime, until: datetime, limit: int
) -> list[CoffeeSaleMatch]:
    """Probe path: coffee sales for any customer, capped with FIRST n."""
    adapter = get_erp_adapter(settings)
    group_ids = parse_coffee_group_ids(settings.coffee_beans_group_ids)
    paid = parse_paid_statuses(settings.erp_paid_statuses)
    query, params = build_coffee_sales_query(
        group_ids=group_ids,
        customer_erp_ids=[],
        since=since,
        until=until,
        paid_statuses=paid,
        all_customers=True,
        row_limit=limit,
    )
    # Adapters only expose find_coffee_sales; call private execute when available.
    execute = getattr(adapter, "_execute_query", None)
    if execute is None:
        raise SystemExit(
            f"Adapter {type(adapter).__name__} cannot run --all-coffee "
            "(needs proxy/direct with _execute_query)"
        )
    rows = execute(query, params)
    return rows_to_matches(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe ERP coffee sales for shop cards.")
    parser.add_argument(
        "--day",
        default="today",
        help="Calendar day YYYY-MM-DD or 'today' (APP_TIMEZONE)",
    )
    parser.add_argument(
        "--customers",
        type=Path,
        default=ROOT / "config" / "test_shop_cards.json",
        help="JSON catalog of shop cards",
    )
    parser.add_argument(
        "--customer-ids",
        default="",
        help="Comma-separated ORGN IDs (overrides --customers file)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "erp-probe",
        help="Output directory for CSV/JSON",
    )
    parser.add_argument(
        "--mode",
        choices=("settings", "mock"),
        default="settings",
        help="settings = use ERP_ACCESS_MODE from env; mock = fake rows for CI",
    )
    parser.add_argument(
        "--all-coffee",
        action="store_true",
        help="Ignore customer filter; return up to --limit coffee lines for the day",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_ALL_COFFEE_LIMIT,
        help=f"Safety cap for --all-coffee (default {DEFAULT_ALL_COFFEE_LIMIT})",
    )
    args = parser.parse_args()

    settings = get_settings()
    day = resolve_day(args.day, settings.app_timezone)
    since, until = day_window(day, settings.app_timezone)

    if args.customer_ids.strip():
        cards = [
            {"id": cid.strip(), "name": cid.strip()}
            for cid in args.customer_ids.split(",")
            if cid.strip()
        ]
    else:
        cards = load_shop_cards(args.customers)

    name_by_id = {c["id"]: c["name"] for c in cards}
    customer_ids = [c["id"] for c in cards]

    print(f"Day: {day.isoformat()} ({settings.app_timezone})")
    print(f"Window: {since.isoformat()} … {until.isoformat()}")

    if args.mode == "mock":
        print("Mode: mock")
        matches = mock_sales_for_day(day, cards)
    elif args.all_coffee:
        print(f"Mode: {settings.erp_access_mode} (--all-coffee limit={args.limit})")
        matches = fetch_all_coffee(settings, since, until, args.limit)
        name_by_id = {m.customer_erp_id: (m.customer_name or m.customer_erp_id) for m in matches}
    else:
        print(f"Mode: {settings.erp_access_mode}")
        print(f"Customers: {len(customer_ids)}")
        adapter = get_erp_adapter(settings)
        matches = adapter.find_coffee_sales(customer_ids, since=since, until=until)

    enriched = enrich_names(matches, name_by_id)
    csv_path, json_path = write_outputs(
        out_dir=args.out, day=day, matches=enriched, name_by_id=name_by_id
    )
    print_summary(enriched, name_by_id)
    print(f"CSV:  {csv_path.resolve()}")
    print(f"JSON: {json_path.resolve()}")


if __name__ == "__main__":
    main()
