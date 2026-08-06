"""Campaign upsert and CSV row import helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Campaign, CampaignKind, CampaignStatus, Promocode, PromocodeStatus
from app.services.promocode_generator import calculate_expires_at, is_valid_promocode


def resolve_expires_at(campaign: Campaign, now: datetime, ttl_days: int) -> datetime:
    """Campaign end wins over TTL so a wave cannot outlive its campaign."""
    if campaign.ends_at is not None:
        return campaign.ends_at
    return calculate_expires_at(now, ttl_days)


def parse_optional_datetime(value: str | None) -> datetime | None:
    if not value or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def upsert_campaign(
    db: Session,
    *,
    code: str,
    name: str,
    starts_at: datetime | None,
    ends_at: datetime | None,
    notes: str | None,
    kind: CampaignKind = CampaignKind.TEST,
    code_prefix: str | None = None,
) -> Campaign:
    existing = db.scalar(select(Campaign).where(Campaign.code == code))
    if existing is not None:
        existing.name = name
        if starts_at is not None:
            existing.starts_at = starts_at
        if ends_at is not None:
            existing.ends_at = ends_at
        if notes is not None:
            existing.notes = notes
        if code_prefix is not None and existing.code_prefix != code_prefix:
            if existing.code_prefix and db.scalar(
                select(Promocode.id).where(Promocode.campaign_id == existing.id).limit(1)
            ):
                raise ValueError(
                    f"Campaign '{code}' already issued codes with prefix "
                    f"'{existing.code_prefix}'; refusing to change it to '{code_prefix}'"
                )
            existing.code_prefix = code_prefix
        if existing.kind != kind:
            raise ValueError(
                f"Campaign '{code}' already exists with kind {existing.kind.value}; "
                f"refusing to switch to {kind.value}"
            )
        if existing.status == CampaignStatus.DRAFT:
            existing.status = CampaignStatus.ACTIVE
        db.flush()
        return existing

    campaign = Campaign(
        id=uuid.uuid4(),
        code=code,
        name=name,
        status=CampaignStatus.ACTIVE,
        kind=kind,
        code_prefix=code_prefix,
        starts_at=starts_at,
        ends_at=ends_at,
        notes=notes,
    )
    db.add(campaign)
    db.flush()
    return campaign


def close_campaign(db: Session, code: str) -> Campaign | None:
    campaign = db.scalar(select(Campaign).where(Campaign.code == code))
    if campaign is None:
        return None
    campaign.status = CampaignStatus.CLOSED
    db.flush()
    return campaign


def import_campaign_rows(
    db: Session,
    *,
    campaign: Campaign,
    rows: list[dict[str, str]],
    ttl_days: int,
) -> tuple[int, int, list[str]]:
    inserted = 0
    skipped = 0
    errors: list[str] = []
    now = datetime.now(UTC)

    for index, row in enumerate(rows, start=2):
        customer = (row.get("customer_erp_id") or "").strip()
        code = (row.get("promocode") or "").strip()
        if not customer or not code:
            errors.append(f"line {index}: missing customer_erp_id or promocode")
            continue
        if not is_valid_promocode(code):
            errors.append(f"line {index}: invalid promocode '{code}' (need 8 digits)")
            continue

        existing = db.scalar(select(Promocode).where(Promocode.promocode == code))
        if existing is not None:
            skipped += 1
            continue

        already_in_campaign = db.scalar(
            select(Promocode.id).where(
                Promocode.campaign_id == campaign.id,
                Promocode.customer_erp_id == customer,
            )
        )
        if already_in_campaign is not None:
            skipped += 1
            continue

        db.add(
            Promocode(
                id=uuid.uuid4(),
                customer_erp_id=customer,
                promocode=code,
                status=PromocodeStatus.ACTIVE,
                campaign_id=campaign.id,
                created_at=now,
                expires_at=resolve_expires_at(campaign, now, ttl_days),
            )
        )
        inserted += 1

    db.flush()
    return inserted, skipped, errors
