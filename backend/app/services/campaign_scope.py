"""Single place that decides which campaigns the app currently serves.

The active kind (TEST or LIVE) is stored in ``app_settings`` and applied to the
cashier, reconcile and fraud paths, so test data can never be closed while the
system runs on real customers and vice versa.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import ACTIVE_CAMPAIGN_KIND_KEY, AppSetting, Campaign, CampaignKind, Promocode

DEFAULT_KIND = CampaignKind.TEST


def get_active_kind(db: Session) -> CampaignKind:
    row = db.get(AppSetting, ACTIVE_CAMPAIGN_KIND_KEY)
    if row is None:
        return DEFAULT_KIND
    try:
        return CampaignKind(row.value)
    except ValueError:
        return DEFAULT_KIND


def set_active_kind(db: Session, kind: CampaignKind, *, actor: str | None = None) -> CampaignKind:
    """Returns the previous kind."""
    row = db.get(AppSetting, ACTIVE_CAMPAIGN_KIND_KEY)
    previous = DEFAULT_KIND
    now = datetime.now(UTC)
    if row is None:
        db.add(
            AppSetting(
                key=ACTIVE_CAMPAIGN_KIND_KEY,
                value=kind.value,
                updated_by=actor,
                updated_at=now,
            )
        )
    else:
        try:
            previous = CampaignKind(row.value)
        except ValueError:
            previous = DEFAULT_KIND
        row.value = kind.value
        row.updated_by = actor
        row.updated_at = now
    db.flush()
    return previous


def in_scope(promocode: Promocode, kind: CampaignKind) -> bool:
    """Promocodes without a campaign are legacy/test data and never LIVE."""
    campaign = promocode.campaign
    if campaign is None:
        return kind == CampaignKind.TEST
    return campaign.kind == kind


def scoped_promocode_query(db: Session, *, kind: CampaignKind | None = None) -> Select:
    """Base select over promocodes limited to the active campaign kind."""
    active = kind or get_active_kind(db)
    query = select(Promocode).join(Campaign, Promocode.campaign_id == Campaign.id, isouter=True)
    if active == CampaignKind.TEST:
        return query.where(
            (Campaign.id.is_(None)) | (Campaign.kind == CampaignKind.TEST),
        )
    return query.where(Campaign.kind == CampaignKind.LIVE)
