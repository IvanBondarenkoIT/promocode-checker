"""Import promocodes for a campaign wave from CSV.

CSV columns (header required): customer_erp_id,promocode
Optional close of a previous campaign: --close-campaign <code>
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

if not os.getenv("DATABASE_URL") and os.getenv("POSTGRES_PASSWORD"):
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "promocode_checker")
    os.environ["DATABASE_URL"] = (
        f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"
    )

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import CampaignKind  # noqa: E402
from app.services.campaign_import import (  # noqa: E402
    close_campaign,
    import_campaign_rows,
    parse_optional_datetime,
    upsert_campaign,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import campaign promocodes from CSV.")
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="CSV with customer_erp_id,promocode",
    )
    parser.add_argument(
        "--campaign-code",
        required=True,
        help="Stable slug, e.g. beans_wave_2026_08",
    )
    parser.add_argument("--campaign-name", required=True, help="Display name shown in UI")
    parser.add_argument(
        "--kind",
        default="TEST",
        choices=["TEST", "LIVE"],
        help="TEST for rehearsals, LIVE for real customers",
    )
    parser.add_argument("--starts-at", default=None, help="ISO datetime (optional)")
    parser.add_argument("--ends-at", default=None, help="ISO datetime (optional)")
    parser.add_argument("--notes", default=None, help="Optional notes")
    parser.add_argument(
        "--close-campaign",
        default=None,
        help="Mark another campaign code as CLOSED before import",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    settings = get_settings()
    with args.file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if (
            not reader.fieldnames
            or "customer_erp_id" not in reader.fieldnames
            or "promocode" not in reader.fieldnames
        ):
            raise SystemExit("CSV must have headers: customer_erp_id,promocode")
        rows = list(reader)

    with SessionLocal() as db:
        if args.close_campaign:
            closed = close_campaign(db, args.close_campaign.strip())
            if closed is None:
                print(f"WARNING: --close-campaign '{args.close_campaign}' not found")
            else:
                print(f"Closed campaign: {closed.code}")

        campaign = upsert_campaign(
            db,
            code=args.campaign_code.strip(),
            name=args.campaign_name.strip(),
            starts_at=parse_optional_datetime(args.starts_at),
            ends_at=parse_optional_datetime(args.ends_at),
            notes=args.notes,
            kind=CampaignKind(args.kind),
        )
        inserted, skipped, errors = import_campaign_rows(
            db,
            campaign=campaign,
            rows=rows,
            ttl_days=settings.promocode_ttl_days,
        )
        campaign_code = campaign.code
        campaign_name = campaign.name
        campaign_id = campaign.id
        db.commit()

    print(f"Campaign: {campaign_code} ({campaign_name}) id={campaign_id}")
    print(f"Inserted: {inserted}")
    print(f"Skipped (already exist): {skipped}")
    if errors:
        print(f"Row errors: {len(errors)}")
        for err in errors[:20]:
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  … and {len(errors) - 20} more")


if __name__ == "__main__":
    main()
