"""Admin CRUD for individual customer cards (promocodes)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.admin_auth import AdminIdentity
from app.core.config import Settings, get_settings
from app.models import Campaign, CampaignStatus, Promocode, PromocodeStatus
from app.schemas.admin import (
    AdminMutationResponse,
    PromocodeCreateDefaultsResponse,
    PromocodeCreateRequest,
    PromocodeDeleteRequest,
    PromocodeDetailResponse,
    PromocodePatchRequest,
)
from app.services.admin_audit import write_admin_audit
from app.services.admin_mutations import AdminMutationError
from app.services.admin_scope import _campaign_summaries
from app.services.admin_tables import _promocode_row_to_dict
from app.services.campaign_scope import get_active_kind
from app.services.promocode_close import lock_promocode_by_id
from app.services.promocode_generator import (
    calculate_expires_at,
    is_valid_promocode,
    promocode_format_hint,
)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _full_snapshot(promocode: Promocode) -> dict[str, Any]:
    return {
        "customer_erp_id": promocode.customer_erp_id,
        "promocode": promocode.promocode,
        "status": promocode.status.value,
        "campaign_id": str(promocode.campaign_id) if promocode.campaign_id else None,
        "customer_card": promocode.customer_card,
        "customer_name": promocode.customer_name,
        "customer_phone": promocode.customer_phone,
        "expires_at": promocode.expires_at.isoformat(),
        "redeemed_at": promocode.redeemed_at.isoformat() if promocode.redeemed_at else None,
    }


def _parse_campaign_id(raw: str | None) -> uuid.UUID | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        return uuid.UUID(str(raw).strip())
    except ValueError as exc:
        raise AdminMutationError("Invalid campaign_id") from exc


def _require_campaign(db: Session, campaign_id: uuid.UUID) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise AdminMutationError("Campaign not found", status_code=404)
    return campaign


def _assert_unique_promocode(
    db: Session,
    code: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    query = select(Promocode.id).where(Promocode.promocode == code)
    if exclude_id is not None:
        query = query.where(Promocode.id != exclude_id)
    if db.scalar(query) is not None:
        raise AdminMutationError("Promocode already exists")


def _assert_unique_campaign_customer(
    db: Session,
    *,
    campaign_id: uuid.UUID | None,
    customer_erp_id: str,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if campaign_id is None:
        return
    query = select(Promocode.id).where(
        Promocode.campaign_id == campaign_id,
        Promocode.customer_erp_id == customer_erp_id,
    )
    if exclude_id is not None:
        query = query.where(Promocode.id != exclude_id)
    if db.scalar(query) is not None:
        raise AdminMutationError("Customer already has a card in this campaign")


def _normalize_code(value: str) -> str:
    code = value.strip()
    if not is_valid_promocode(code):
        raise AdminMutationError(f"Promocode must be {promocode_format_hint()}")
    return code


def _detail(promocode: Promocode) -> PromocodeDetailResponse:
    payload = _promocode_row_to_dict(promocode)
    return PromocodeDetailResponse(
        id=str(payload["id"]),
        customer_erp_id=payload["customer_erp_id"],
        promocode=payload["promocode"],
        status=payload["status"],
        campaign_id=payload.get("campaign_id"),
        campaign_code=payload.get("campaign_code"),
        campaign_name=payload.get("campaign_name"),
        campaign_kind=payload.get("campaign_kind"),
        customer_card=payload.get("customer_card"),
        customer_name=payload.get("customer_name"),
        customer_phone=payload.get("customer_phone"),
        created_at=payload["created_at"],
        expires_at=payload["expires_at"],
        redeemed_at=payload.get("redeemed_at"),
    )


def get_promocode_detail(db: Session, promocode_id: uuid.UUID) -> PromocodeDetailResponse:
    promocode = db.scalar(
        select(Promocode)
        .options(joinedload(Promocode.campaign))
        .where(Promocode.id == promocode_id)
    )
    if promocode is None:
        raise AdminMutationError("Promocode not found", status_code=404)
    return _detail(promocode)


def get_create_defaults(
    db: Session,
    *,
    settings: Settings | None = None,
) -> PromocodeCreateDefaultsResponse:
    cfg = settings or get_settings()
    active_kind = get_active_kind(db)
    campaigns = _campaign_summaries(db)
    default_campaign_id: str | None = None
    preferred = db.scalar(
        select(Campaign)
        .where(
            Campaign.kind == active_kind,
            Campaign.status == CampaignStatus.ACTIVE,
        )
        .order_by(Campaign.created_at.desc())
        .limit(1)
    )
    if preferred is not None:
        default_campaign_id = str(preferred.id)
    now = datetime.now(UTC)
    return PromocodeCreateDefaultsResponse(
        active_campaign_kind=active_kind.value,
        default_campaign_id=default_campaign_id,
        status=PromocodeStatus.ACTIVE.value,
        expires_at=calculate_expires_at(now, cfg.promocode_ttl_days).isoformat(),
        promocode_ttl_days=cfg.promocode_ttl_days,
        campaigns=campaigns,
    )


def create_promocode(
    db: Session,
    *,
    actor: AdminIdentity,
    payload: PromocodeCreateRequest,
    settings: Settings | None = None,
) -> AdminMutationResponse:
    cfg = settings or get_settings()
    code = _normalize_code(payload.promocode)
    erp_id = payload.customer_erp_id.strip()
    if not erp_id:
        raise AdminMutationError("customer_erp_id is required")

    campaign_id = _parse_campaign_id(payload.campaign_id)
    if campaign_id is not None:
        _require_campaign(db, campaign_id)

    _assert_unique_promocode(db, code)
    _assert_unique_campaign_customer(db, campaign_id=campaign_id, customer_erp_id=erp_id)

    status = PromocodeStatus.ACTIVE
    if payload.status is not None:
        try:
            status = PromocodeStatus(payload.status.strip().upper())
        except ValueError as exc:
            raise AdminMutationError("Invalid promocode status") from exc

    now = datetime.now(UTC)
    expires_at = (
        _ensure_aware(payload.expires_at)
        if payload.expires_at is not None
        else calculate_expires_at(now, cfg.promocode_ttl_days)
    )
    customer_card = (payload.customer_card or "").strip() or code
    customer_name = (payload.customer_name or "").strip() or None
    customer_phone = (payload.customer_phone or "").strip() or None

    promocode = Promocode(
        customer_erp_id=erp_id,
        promocode=code,
        status=status,
        campaign_id=campaign_id,
        customer_card=customer_card,
        customer_name=customer_name,
        customer_phone=customer_phone,
        created_at=now,
        expires_at=expires_at,
        redeemed_at=now if status == PromocodeStatus.USED else None,
    )
    db.add(promocode)
    try:
        db.flush()
    except IntegrityError as exc:
        raise AdminMutationError("Promocode conflicts with an existing card") from exc

    new_values = _full_snapshot(promocode)
    audit = write_admin_audit(
        db,
        actor=actor,
        entity_name="promocodes",
        entity_id=str(promocode.id),
        promocode_id=promocode.id,
        action="admin_create",
        reason=payload.reason,
        old_values={},
        new_values=new_values,
    )
    db.flush()
    return AdminMutationResponse(
        entity="promocodes",
        entity_id=str(promocode.id),
        audit_log_id=audit.id,
    )


def patch_promocode_full(
    db: Session,
    *,
    actor: AdminIdentity,
    promocode_id: uuid.UUID,
    payload: PromocodePatchRequest,
) -> AdminMutationResponse:
    promocode = lock_promocode_by_id(db, promocode_id)
    if promocode is None:
        raise AdminMutationError("Promocode not found", status_code=404)

    old_values = _full_snapshot(promocode)
    new_values = dict(old_values)
    changed = False

    if payload.status is not None:
        try:
            new_status = PromocodeStatus(payload.status.strip().upper())
        except ValueError as exc:
            raise AdminMutationError("Invalid promocode status") from exc
        if new_status != promocode.status:
            promocode.status = new_status
            new_values["status"] = new_status.value
            changed = True
            if new_status == PromocodeStatus.ACTIVE:
                promocode.redeemed_at = None
                new_values["redeemed_at"] = None
            elif new_status == PromocodeStatus.USED and promocode.redeemed_at is None:
                promocode.redeemed_at = datetime.now(UTC)
                new_values["redeemed_at"] = promocode.redeemed_at.isoformat()

    if payload.expires_at is not None:
        expires_at = _ensure_aware(payload.expires_at)
        if promocode.expires_at != expires_at:
            promocode.expires_at = expires_at
            new_values["expires_at"] = expires_at.isoformat()
            changed = True

    if payload.clear_campaign:
        if promocode.campaign_id is not None:
            promocode.campaign_id = None
            new_values["campaign_id"] = None
            changed = True
    elif payload.campaign_id is not None:
        campaign_id = _parse_campaign_id(payload.campaign_id)
        if campaign_id is None:
            raise AdminMutationError("Invalid campaign_id")
        _require_campaign(db, campaign_id)
        if promocode.campaign_id != campaign_id:
            _assert_unique_campaign_customer(
                db,
                campaign_id=campaign_id,
                customer_erp_id=payload.customer_erp_id.strip()
                if payload.customer_erp_id
                else promocode.customer_erp_id,
                exclude_id=promocode.id,
            )
            promocode.campaign_id = campaign_id
            new_values["campaign_id"] = str(campaign_id)
            changed = True

    if payload.customer_erp_id is not None:
        erp_id = payload.customer_erp_id.strip()
        if not erp_id:
            raise AdminMutationError("customer_erp_id cannot be empty")
        if erp_id != promocode.customer_erp_id:
            _assert_unique_campaign_customer(
                db,
                campaign_id=promocode.campaign_id,
                customer_erp_id=erp_id,
                exclude_id=promocode.id,
            )
            promocode.customer_erp_id = erp_id
            new_values["customer_erp_id"] = erp_id
            changed = True

    if payload.promocode is not None:
        code = _normalize_code(payload.promocode)
        if code != promocode.promocode:
            _assert_unique_promocode(db, code, exclude_id=promocode.id)
            promocode.promocode = code
            new_values["promocode"] = code
            changed = True

    if payload.customer_card is not None:
        card = payload.customer_card.strip() or None
        if card != promocode.customer_card:
            promocode.customer_card = card
            new_values["customer_card"] = card
            changed = True

    if payload.customer_name is not None:
        name = payload.customer_name.strip() or None
        if name != promocode.customer_name:
            promocode.customer_name = name
            new_values["customer_name"] = name
            changed = True

    if payload.customer_phone is not None:
        phone = payload.customer_phone.strip() or None
        if phone != promocode.customer_phone:
            promocode.customer_phone = phone
            new_values["customer_phone"] = phone
            changed = True

    if not changed:
        raise AdminMutationError("No changes requested")

    try:
        db.flush()
    except IntegrityError as exc:
        raise AdminMutationError("Promocode conflicts with an existing card") from exc

    audit = write_admin_audit(
        db,
        actor=actor,
        entity_name="promocodes",
        entity_id=str(promocode.id),
        promocode_id=promocode.id,
        action="admin_patch",
        reason=payload.reason,
        old_values=old_values,
        new_values=new_values,
    )
    db.flush()
    return AdminMutationResponse(
        entity="promocodes",
        entity_id=str(promocode.id),
        audit_log_id=audit.id,
    )


def delete_promocode(
    db: Session,
    *,
    actor: AdminIdentity,
    promocode_id: uuid.UUID,
    payload: PromocodeDeleteRequest,
) -> AdminMutationResponse:
    promocode = lock_promocode_by_id(db, promocode_id)
    if promocode is None:
        raise AdminMutationError("Promocode not found", status_code=404)

    old_values = _full_snapshot(promocode)
    entity_id = str(promocode.id)
    audit = write_admin_audit(
        db,
        actor=actor,
        entity_name="promocodes",
        entity_id=entity_id,
        promocode_id=promocode.id,
        action="admin_delete",
        reason=payload.reason,
        old_values=old_values,
        new_values={},
    )
    db.delete(promocode)
    db.flush()
    return AdminMutationResponse(
        entity="promocodes",
        entity_id=entity_id,
        audit_log_id=audit.id,
    )
