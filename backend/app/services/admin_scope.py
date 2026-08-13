"""Admin-facing read/write of the global campaign scope switch."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.admin_auth import AdminIdentity
from app.models import Campaign, CampaignKind, Promocode, PromocodeStatus
from app.schemas.admin import ActiveScopeResponse, CampaignSummary
from app.services.admin_audit import write_admin_audit
from app.services.campaign_scope import get_active_kind, set_active_kind
from app.services.telegram import send_alert
from app.services.telegram_messages import msg_scope_switched


class ScopeUpdateError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _campaign_summaries(db: Session) -> list[CampaignSummary]:
    rows = db.execute(
        select(
            Campaign.id,
            Campaign.code,
            Campaign.name,
            Campaign.kind,
            Campaign.status,
            func.count(Promocode.id),
            func.count(Promocode.id).filter(Promocode.status == PromocodeStatus.USED),
        )
        .join(Promocode, Promocode.campaign_id == Campaign.id, isouter=True)
        .group_by(
            Campaign.id,
            Campaign.code,
            Campaign.name,
            Campaign.kind,
            Campaign.status,
            Campaign.created_at,
        )
        .order_by(Campaign.created_at.desc())
    ).all()
    return [
        CampaignSummary(
            id=str(campaign_id),
            code=code,
            name=name,
            kind=kind.value,
            status=status.value,
            issued=int(issued or 0),
            used=int(used or 0),
        )
        for campaign_id, code, name, kind, status, issued, used in rows
    ]


def get_active_scope(db: Session) -> ActiveScopeResponse:
    return ActiveScopeResponse(
        active_campaign_kind=get_active_kind(db).value,
        campaigns=_campaign_summaries(db),
    )


def update_active_scope(
    db: Session,
    *,
    actor: AdminIdentity,
    requested_kind: str,
    reason: str,
) -> ActiveScopeResponse:
    try:
        kind = CampaignKind(requested_kind.strip().upper())
    except ValueError as exc:
        raise ScopeUpdateError("Invalid campaign kind (expected TEST or LIVE)") from exc

    current = get_active_kind(db)
    if current == kind:
        raise ScopeUpdateError("Active campaign kind unchanged")

    previous = set_active_kind(db, kind, actor=actor.username)
    write_admin_audit(
        db,
        actor=actor,
        entity_name="app_settings",
        entity_id="active_campaign_kind",
        promocode_id=None,
        action="scope_switch",
        reason=reason,
        old_values={"active_campaign_kind": previous.value},
        new_values={"active_campaign_kind": kind.value},
    )
    send_alert(
        db,
        event_type="scope_switched",
        dedup_key=f"scope_switched:{previous.value}:{kind.value}:{actor.username}",
        message=msg_scope_switched(
            previous=previous.value,
            current=kind.value,
            actor=actor.username,
        ),
        audience="errors",
        skip_dedup=True,
    )
    db.flush()
    return get_active_scope(db)
