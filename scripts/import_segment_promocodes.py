"""Import a customer segment and issue generated promocodes.

CSV: segmentation export with a `customer_id` column (ERP ORGN id).
Codes are generated here, prefixed per campaign; the file must not contain them.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
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

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Campaign, CampaignKind  # noqa: E402
from app.services.campaign_import import parse_optional_datetime, upsert_campaign  # noqa: E402
from app.services.segment_import import (  # noqa: E402
    import_segment,
    read_segment_csv,
    rollback_campaign_codes,
    write_issued_csv,
)
from app.services.telegram import send_alert  # noqa: E402
from app.services.telegram_messages import msg_campaign_import  # noqa: E402
from sqlalchemy import select  # noqa: E402

EXPORT_DIR = ROOT / "artifacts" / "campaigns"


def _rollback(campaign_code: str) -> int:
    with SessionLocal() as db:
        campaign = db.scalar(select(Campaign).where(Campaign.code == campaign_code))
        if campaign is None:
            print(f"Campaign not found: {campaign_code}", file=sys.stderr)
            return 1
        deleted, kept = rollback_campaign_codes(db, campaign)
        db.commit()
    print(f"Rollback {campaign_code}: deleted={deleted} kept_used_or_scanned={kept}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue promocodes for a customer segment.")
    parser.add_argument("--file", type=Path, help="Segment CSV with a customer_id column")
    parser.add_argument("--campaign-code", help="Stable slug, e.g. beans_1_2kg_preprod")
    parser.add_argument("--campaign-name", help="Display name shown in UI")
    parser.add_argument(
        "--kind",
        default=CampaignKind.TEST.value,
        choices=[CampaignKind.TEST.value, CampaignKind.LIVE.value],
        help="TEST for rehearsals, LIVE for real customers",
    )
    parser.add_argument("--code-prefix", default=None, help="Leading digit reserved for this wave")
    parser.add_argument("--starts-at", default=None, help="ISO datetime (optional)")
    parser.add_argument("--ends-at", default=None, help="ISO datetime (optional)")
    parser.add_argument("--notes", default=None, help="Optional notes")
    parser.add_argument("--dry-run", action="store_true", help="Report only, write nothing")
    parser.add_argument("--rollback-campaign", default=None, help="Delete untouched codes instead")
    args = parser.parse_args()

    if args.rollback_campaign:
        return _rollback(args.rollback_campaign.strip())

    missing = [
        flag
        for flag, value in (
            ("--file", args.file),
            ("--campaign-code", args.campaign_code),
            ("--campaign-name", args.campaign_name),
        )
        if not value
    ]
    if missing:
        parser.error(f"missing required arguments: {', '.join(missing)}")
    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    settings = get_settings()
    rows, read_errors = read_segment_csv(args.file)
    print(f"Segment rows: {len(rows)} (file errors: {len(read_errors)})")
    for err in read_errors[:20]:
        print(f"  - {err}")

    with SessionLocal() as db:
        campaign = upsert_campaign(
            db,
            code=args.campaign_code.strip(),
            name=args.campaign_name.strip(),
            starts_at=parse_optional_datetime(args.starts_at),
            ends_at=parse_optional_datetime(args.ends_at),
            notes=args.notes,
            kind=CampaignKind(args.kind),
            code_prefix=(args.code_prefix or "").strip() or None,
        )
        result = import_segment(
            db,
            campaign=campaign,
            rows=rows,
            ttl_days=settings.promocode_ttl_days,
            dry_run=args.dry_run,
        )
        campaign_code = campaign.code
        campaign_name = campaign.name
        campaign_kind = campaign.kind.value

        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        suffix = "dryrun" if args.dry_run else "issued"
        export_path = EXPORT_DIR / f"{campaign_code}_{suffix}_{stamp}.csv"
        if result.created:
            write_issued_csv(export_path, result.created)

        if not args.dry_run:
            send_alert(
                db,
                event_type="campaign_import",
                dedup_key=f"campaign_import:{campaign_code}:{stamp}",
                message=msg_campaign_import(
                    campaign_code=campaign_code,
                    campaign_name=campaign_name,
                    campaign_kind=campaign_kind,
                    created=result.created_count,
                    skipped=result.skipped_existing,
                    errors=len(result.errors) + len(read_errors),
                    dry_run=False,
                ),
                settings=settings,
                audience="errors",
                skip_dedup=True,
            )
            db.commit()
        else:
            db.rollback()

    print(f"Campaign: {campaign_code} ({campaign_name}) kind={campaign_kind}")
    print(f"Issued: {result.created_count}{' (dry-run, nothing written)' if args.dry_run else ''}")
    print(f"Skipped (already in campaign): {result.skipped_existing}")
    if result.created:
        print(f"Export: {export_path}")
    all_errors = read_errors + result.errors
    if all_errors:
        print(f"Errors: {len(all_errors)}")
        for err in all_errors[:20]:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
