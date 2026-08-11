"""Remap campaign promocodes to loyalty card numbers (promocode = customer_card).

Use after migration 006 when older segment imports issued random 8-digit codes.
"""

from __future__ import annotations

import argparse
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
    os.environ["DATABASE_URL"] = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"

from app.db.session import SessionLocal  # noqa: E402
from app.models import Campaign  # noqa: E402
from app.services.promocode_remap import remap_campaign_promocodes_to_card  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set promocode = customer_card for an existing campaign."
    )
    parser.add_argument("--campaign-code", required=True, help="Campaign slug to remap")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report only; do not write",
    )
    args = parser.parse_args()
    campaign_code = args.campaign_code.strip()

    with SessionLocal() as db:
        campaign = db.scalar(select(Campaign).where(Campaign.code == campaign_code))
        if campaign is None:
            print(f"Campaign not found: {campaign_code}", file=sys.stderr)
            return 1

        result = remap_campaign_promocodes_to_card(db, campaign, dry_run=args.dry_run)
        if args.dry_run:
            db.rollback()
        else:
            db.commit()

    print(f"Campaign: {campaign_code}")
    print(f"Already ok (promocode == card): {result.already_ok}")
    print(f"Remapped: {result.remapped_count}{' (dry-run)' if args.dry_run else ''}")
    for customer, old, new in result.remapped[:20]:
        print(f"  - {customer}: {old} -> {new}")
    if len(result.remapped) > 20:
        print(f"  ... and {len(result.remapped) - 20} more")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for err in result.errors[:30]:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
