from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdminAuditLog,
    Campaign,
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


def _promocode_row_to_dict(row: Promocode) -> dict[str, Any]:
    payload = _row_to_dict(row)
    campaign = row.campaign
    payload["campaign_code"] = campaign.code if campaign is not None else None
    payload["campaign_name"] = campaign.name if campaign is not None else None
    return payload


_TABLE_MODELS = {
    AdminTableName.PROMOCODES: Promocode,
    AdminTableName.CAMPAIGNS: Campaign,
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
    query = select(model).order_by(model.id.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
    if table == AdminTableName.PROMOCODES:
        query = query.options(joinedload(Promocode.campaign))
    rows = list(db.scalars(query).unique().all())
    serialized = (
        [_promocode_row_to_dict(row) for row in rows]
        if table == AdminTableName.PROMOCODES
        else [_row_to_dict(row) for row in rows]
    )
    return TableListResponse(
        table=table.value,
        total=total,
        limit=limit,
        offset=offset,
        rows=serialized,
    )
