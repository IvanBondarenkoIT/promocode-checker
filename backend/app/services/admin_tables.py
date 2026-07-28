from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AdminAuditLog,
    CheckerLog,
    FraudWarning,
    Promocode,
    TelegramNotificationLog,
)
from app.schemas.admin import AdminTableName, TableListResponse


def _serialize_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _row_to_dict(row) -> dict[str, Any]:
    return {
        column.name: _serialize_value(getattr(row, column.name))
        for column in row.__table__.columns
    }


_TABLE_MODELS = {
    AdminTableName.PROMOCODES: Promocode,
    AdminTableName.CHECKER_LOGS: CheckerLog,
    AdminTableName.FRAUD_WARNINGS: FraudWarning,
    AdminTableName.ADMIN_AUDIT_LOGS: AdminAuditLog,
    AdminTableName.TELEGRAM_NOTIFICATION_LOGS: TelegramNotificationLog,
}


def list_table_rows(
    db: Session,
    *,
    table: AdminTableName,
    limit: int = 50,
    offset: int = 0,
) -> TableListResponse:
    model = _TABLE_MODELS[table]
    total = db.scalar(select(func.count()).select_from(model)) or 0
    rows = list(
        db.scalars(
            select(model).order_by(model.id.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
        ).all()
    )
    return TableListResponse(
        table=table.value,
        total=total,
        limit=limit,
        offset=offset,
        rows=[_row_to_dict(row) for row in rows],
    )
