"""Export Code128 PNG images for promocodes (dummy seed or a real campaign)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

if not os.getenv("DATABASE_URL") and os.getenv("POSTGRES_PASSWORD"):
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "promocode_checker")
    os.environ["DATABASE_URL"] = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"

from app.services.barcode import render_code128_png  # noqa: E402
from seed_promocodes import DUMMY_PROMOCODES  # noqa: E402


def _campaign_codes(campaign_code: str) -> list[str]:
    from app.db.session import SessionLocal
    from app.models import Campaign, Promocode
    from sqlalchemy import select

    with SessionLocal() as db:
        campaign = db.scalar(select(Campaign).where(Campaign.code == campaign_code))
        if campaign is None:
            raise SystemExit(f"Campaign not found: {campaign_code}")
        return list(
            db.scalars(
                select(Promocode.promocode)
                .where(Promocode.campaign_id == campaign.id)
                .order_by(Promocode.promocode)
            ).all()
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Write promocode barcode PNGs.")
    parser.add_argument(
        "--campaign-code",
        default=None,
        help="Export every promocode of this campaign instead of the dummy seed list",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for PNG files",
    )
    args = parser.parse_args()

    if args.campaign_code:
        codes = _campaign_codes(args.campaign_code.strip())
        default_out = ROOT / "artifacts" / "campaigns" / f"{args.campaign_code.strip()}-barcodes"
    else:
        codes = [item.promocode for item in DUMMY_PROMOCODES]
        default_out = ROOT / "artifacts" / "dummy-barcodes"

    out_dir: Path = args.out or default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    for code in codes:
        (out_dir / f"{code}.png").write_bytes(render_code128_png(code))

    print(f"Wrote {len(codes)} barcode PNG(s) to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
