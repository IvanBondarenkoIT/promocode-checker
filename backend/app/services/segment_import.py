"""Import a customer segment and issue one generated promocode per customer.

Input is the segmentation export (``customer_id`` = ERP ORGN id). Codes are not
supplied by the file: each customer gets a random 8-digit code carrying the
campaign prefix, so campaigns never share a code range.
"""

from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Campaign, CheckerLog, Promocode, PromocodeStatus
from app.services.campaign_import import resolve_expires_at
from app.services.promocode_generator import generate_unique_promocode

REQUIRED_COLUMN = "customer_id"
CARD_COLUMN = "customer_name"
FULL_NAME_COLUMN = "customer_full_name"
PHONE_COLUMN = "phone"

ISSUED_HEADER = [
    "customer_erp_id",
    "customer_card",
    "customer_name",
    "customer_phone",
    "promocode",
    "expires_at",
]


@dataclass
class SegmentRow:
    customer_erp_id: str
    card: str | None = None
    name: str | None = None
    phone: str | None = None


@dataclass
class IssuedCode:
    customer_erp_id: str
    card: str | None
    name: str | None
    phone: str | None
    promocode: str
    expires_at: datetime


@dataclass
class SegmentImportResult:
    created: list[IssuedCode] = field(default_factory=list)
    skipped_existing: int = 0
    duplicate_rows: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        return len(self.created)


def _clean(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def read_segment_csv(path: Path) -> tuple[list[SegmentRow], list[str]]:
    """Parse the segment export. Returns (rows, errors); duplicates are kept out."""
    rows: list[SegmentRow] = []
    errors: list[str] = []
    seen: set[str] = set()

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or REQUIRED_COLUMN not in reader.fieldnames:
            raise ValueError(f"CSV must contain a '{REQUIRED_COLUMN}' column")

        for index, raw in enumerate(reader, start=2):
            customer = _clean(raw.get(REQUIRED_COLUMN))
            if not customer:
                errors.append(f"line {index}: empty {REQUIRED_COLUMN}")
                continue
            if customer in seen:
                errors.append(f"line {index}: duplicate {REQUIRED_COLUMN} '{customer}' in file")
                continue
            seen.add(customer)
            rows.append(
                SegmentRow(
                    customer_erp_id=customer,
                    card=_clean(raw.get(CARD_COLUMN)),
                    name=_clean(raw.get(FULL_NAME_COLUMN)),
                    phone=_clean(raw.get(PHONE_COLUMN)),
                )
            )

    return rows, errors


def import_segment(
    db: Session,
    *,
    campaign: Campaign,
    rows: list[SegmentRow],
    ttl_days: int,
    now: datetime | None = None,
    dry_run: bool = False,
) -> SegmentImportResult:
    """Issue one code per new customer in the campaign. Re-runs are safe."""
    result = SegmentImportResult()
    current = now or datetime.now(UTC)
    expires_at = resolve_expires_at(campaign, current, ttl_days)
    reserved: set[str] = set()

    for row in rows:
        existing = db.scalar(
            select(Promocode).where(
                Promocode.campaign_id == campaign.id,
                Promocode.customer_erp_id == row.customer_erp_id,
            )
        )
        if existing is not None:
            result.skipped_existing += 1
            continue

        try:
            code = generate_unique_promocode(
                db,
                prefix=campaign.code_prefix,
                reserved=reserved,
            )
        except RuntimeError as exc:
            result.errors.append(f"customer {row.customer_erp_id}: {exc}")
            continue

        result.created.append(
            IssuedCode(
                customer_erp_id=row.customer_erp_id,
                card=row.card,
                name=row.name,
                phone=row.phone,
                promocode=code,
                expires_at=expires_at,
            )
        )

        if dry_run:
            continue

        db.add(
            Promocode(
                id=uuid.uuid4(),
                customer_erp_id=row.customer_erp_id,
                promocode=code,
                status=PromocodeStatus.ACTIVE,
                campaign_id=campaign.id,
                customer_card=row.card,
                customer_name=row.name,
                customer_phone=row.phone,
                created_at=current,
                expires_at=expires_at,
            )
        )

    if not dry_run:
        db.flush()
    return result


def write_issued_csv(path: Path, issued: list[IssuedCode]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(ISSUED_HEADER)
        for item in issued:
            writer.writerow(
                [
                    item.customer_erp_id,
                    item.card or "",
                    item.name or "",
                    item.phone or "",
                    item.promocode,
                    item.expires_at.isoformat(),
                ]
            )
    return path


def rollback_campaign_codes(db: Session, campaign: Campaign) -> tuple[int, int]:
    """Delete untouched ACTIVE codes of a campaign.

    Returns (deleted, kept). Codes that were scanned or redeemed are kept so the
    audit trail stays intact.
    """
    codes = list(db.scalars(select(Promocode).where(Promocode.campaign_id == campaign.id)).all())
    deleted = 0
    kept = 0
    for promo in codes:
        touched = promo.status != PromocodeStatus.ACTIVE or promo.redeemed_at is not None
        if not touched:
            has_log = db.scalar(select(CheckerLog.id).where(CheckerLog.promocode_id == promo.id))
            touched = has_log is not None
        if touched:
            kept += 1
            continue
        db.delete(promo)
        deleted += 1
    db.flush()
    return deleted, kept
