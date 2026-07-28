"""Write admin audit rows for controlled mutations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.admin_auth import AdminIdentity
from app.models import AdminAuditLog, AdminRole


def write_admin_audit(
    db: Session,
    *,
    actor: AdminIdentity,
    entity_name: str,
    entity_id: str,
    action: str,
    reason: str,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    promocode_id: uuid.UUID | None = None,
) -> AdminAuditLog:
    log = AdminAuditLog(
        actor_username=actor.username,
        actor_role=AdminRole(actor.role.value),
        entity_name=entity_name,
        entity_id=entity_id,
        promocode_id=promocode_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        reason=reason,
    )
    db.add(log)
    db.flush()
    return log
