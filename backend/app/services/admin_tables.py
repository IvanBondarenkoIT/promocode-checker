from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdminAuditLog,
    Campaign,
    CampaignKind,
    CheckerLog,
    FraudWarning,
    Promocode,
    SaleObservation,
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
    payload["campaign_kind"] = campaign.kind.value if campaign is not None else None
    return payload


_TABLE_MODELS = {
    AdminTableName.PROMOCODES: Promocode,
    AdminTableName.CAMPAIGNS: Campaign,
    AdminTableName.CHECKER_LOGS: CheckerLog,
    AdminTableName.FRAUD_WARNINGS: FraudWarning,
    AdminTableName.SALE_OBSERVATIONS: SaleObservation,
    AdminTableName.ADMIN_AUDIT_LOGS: AdminAuditLog,
    AdminTableName.TELEGRAM_NOTIFICATION_LOGS: TelegramNotificationLog,
}


def _apply_filters(
    query,
    *,
    table: AdminTableName,
    campaign_code: str | None,
    kind: CampaignKind | None,
    status: str | None,
    search: str | None,
):
    if table == AdminTableName.PROMOCODES:
        if campaign_code or kind is not None:
            query = query.join(Campaign, Promocode.campaign_id == Campaign.id)
            if campaign_code:
                query = query.where(Campaign.code == campaign_code)
            if kind is not None:
                query = query.where(Campaign.kind == kind)
        if status:
            query = query.where(Promocode.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Promocode.promocode.ilike(pattern),
                    Promocode.customer_erp_id.ilike(pattern),
                    Promocode.customer_card.ilike(pattern),
                    Promocode.customer_name.ilike(pattern),
                )
            )
        return query

    if table == AdminTableName.CAMPAIGNS:
        if campaign_code:
            query = query.where(Campaign.code == campaign_code)
        if kind is not None:
            query = query.where(Campaign.kind == kind)
        if status:
            query = query.where(Campaign.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(or_(Campaign.code.ilike(pattern), Campaign.name.ilike(pattern)))
        return query

    if table == AdminTableName.CHECKER_LOGS:
        if search:
            query = query.where(CheckerLog.scanned_code.ilike(f"%{search}%"))
        if status:
            query = query.where(CheckerLog.action_type == status)
        return query

    if table == AdminTableName.FRAUD_WARNINGS:
        if status:
            query = query.where(FraudWarning.status == status)
        if search:
            query = query.where(FraudWarning.promocode_value.ilike(f"%{search}%"))
        return query

    if table == AdminTableName.SALE_OBSERVATIONS:
        if status:
            query = query.where(SaleObservation.verdict == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    SaleObservation.promocode_value.ilike(pattern),
                    SaleObservation.customer_erp_id.ilike(pattern),
                    SaleObservation.order_id.ilike(pattern),
                    SaleObservation.customer_name.ilike(pattern),
                )
            )
        return query

    return query


def list_table_rows(
    db: Session,
    *,
    table: AdminTableName,
    limit: int = 50,
    offset: int = 0,
    campaign_code: str | None = None,
    kind: CampaignKind | None = None,
    status: str | None = None,
    search: str | None = None,
) -> TableListResponse:
    model = _TABLE_MODELS[table]

    filters = {
        "table": table,
        "campaign_code": (campaign_code or "").strip() or None,
        "kind": kind,
        "status": (status or "").strip() or None,
        "search": (search or "").strip() or None,
    }

    count_query = _apply_filters(select(func.count()).select_from(model), **filters)
    total = db.scalar(count_query) or 0

    query = _apply_filters(select(model), **filters)
    query = query.order_by(model.id.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
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
