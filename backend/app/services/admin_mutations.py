from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.admin_auth import AdminIdentity
from app.models import FraudWarning, FraudWarningStatus
from app.schemas.admin import AdminMutationResponse, FraudWarningPatchRequest, PromocodePatchRequest
from app.services.admin_audit import write_admin_audit


class AdminMutationError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def patch_promocode(
    db: Session,
    *,
    actor: AdminIdentity,
    promocode_id: uuid.UUID,
    payload: PromocodePatchRequest,
) -> AdminMutationResponse:
    # Full field patch lives in admin_promocodes (create/delete share helpers).
    from app.services.admin_promocodes import patch_promocode_full

    return patch_promocode_full(
        db,
        actor=actor,
        promocode_id=promocode_id,
        payload=payload,
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
