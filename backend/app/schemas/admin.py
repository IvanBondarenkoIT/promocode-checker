from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class AdminLoginResponse(BaseModel):
    token: str
    username: str
    role: str


class AdminMeResponse(BaseModel):
    username: str
    role: str


class DashboardResponse(BaseModel):
    promocodes_active: int
    promocodes_used: int
    promocodes_expired: int
    scans_last_24h: int
    auto_closes_total: int
    fraud_open: int
    telegram_sent_last_24h: int


class TableListResponse(BaseModel):
    table: str
    total: int
    limit: int
    offset: int
    rows: list[dict]


class PromocodePatchRequest(BaseModel):
    status: str | None = None
    expires_at: datetime | None = None
    reason: str = Field(min_length=3, max_length=2000)


class FraudWarningPatchRequest(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=3, max_length=2000)


class AdminMutationResponse(BaseModel):
    ok: bool = True
    entity: str
    entity_id: str
    audit_log_id: int | None = None


class AdminTableName(StrEnum):
    PROMOCODES = "promocodes"
    CHECKER_LOGS = "checker_logs"
    FRAUD_WARNINGS = "fraud_warnings"
    ADMIN_AUDIT_LOGS = "admin_audit_logs"
    TELEGRAM_NOTIFICATION_LOGS = "telegram_notification_logs"
