from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.admin_auth import AdminIdentity
from app.models import FraudWarning, FraudWarningStatus, Promocode, PromocodeStatus
from app.schemas.admin import AdminMutationResponse, FraudWarningPatchRequest, PromocodePatchRequest
from app.services.admin_audit import write_admin_audit
from app.services.promocode_close import lock_promocode_by_id


class AdminMutationError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _promocode_snapshot(promocode: Promocode) -> dict[str, Any]:
    return {
        "status": promocode.status.value,
        "expires_at": promocode.expires_at.isoformat(),
        "redeemed_at": promocode.redeemed_at.isoformat() if promocode.redeemed_at else None,
    }


def patch_promocode(
    db: Session,
    *,
    actor: AdminIdentity,
    promocode_id: uuid.UUID,
    payload: PromocodePatchRequest,
) -> AdminMutationResponse:
    promocode = lock_promocode_by_id(db, promocode_id)
    if promocode is None:
        raise AdminMutationError("Promocode not found", status_code=404)

    old_values = _promocode_snapshot(promocode)
    new_values = dict(old_values)
    changed = False

    if payload.status is not None:
        try:
            new_status = PromocodeStatus(payload.status.upper())
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
        expires_at = payload.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if promocode.expires_at != expires_at:
            promocode.expires_at = expires_at
            new_values["expires_at"] = expires_at.isoformat()
            changed = True

    if not changed:
        raise AdminMutationError("No changes requested")

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


def patch_fraud_warning(
    db: Session,
    *,
    actor: AdminIdentity,
    warning_id: int,
    payload: FraudWarningPatchRequest,
) -> AdminMutationResponse:
    warning = db.get(FraudWarning, warning_id)
    if warning is None:
        raise AdminMutationError("Fraud warning not found", status_code=404)

    try:
        new_status = FraudWarningStatus(payload.status.upper())
    except ValueError as exc:
        raise AdminMutationError("Invalid fraud warning status") from exc

    old_values = {"status": warning.status.value, "reviewed_by": warning.reviewed_by}
    if new_status == warning.status:
        raise AdminMutationError("Status unchanged")

    warning.status = new_status
    warning.reviewed_by = actor.username
    warning.reviewed_at = datetime.now(UTC)
    new_values = {
        "status": warning.status.value,
        "reviewed_by": warning.reviewed_by,
        "reviewed_at": warning.reviewed_at.isoformat(),
    }

    audit = write_admin_audit(
        db,
        actor=actor,
        entity_name="fraud_warnings",
        entity_id=str(warning.id),
        promocode_id=warning.promocode_id,
        action="admin_review",
        reason=payload.reason,
        old_values=old_values,
        new_values=new_values,
    )
    db.flush()
    return AdminMutationResponse(
        entity="fraud_warnings",
        entity_id=str(warning.id),
        audit_log_id=audit.id,
    )
