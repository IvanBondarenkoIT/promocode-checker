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
    active_campaign_kind: str = "TEST"
    enforcement_mode: str = "monitor"
    promo_min_coffee_kg: float = 2.0
    sale_observations_24h: int = 0
    sale_qualified_24h: int = 0


class TableListResponse(BaseModel):
    table: str
    total: int
    limit: int
    offset: int
    rows: list[dict]


class FraudWarningPatchRequest(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=3, max_length=2000)


class CampaignSummary(BaseModel):
    id: str | None = None
    code: str
    name: str
    kind: str
    status: str
    issued: int
    used: int


class ActiveScopeResponse(BaseModel):
    active_campaign_kind: str
    campaigns: list[CampaignSummary] = []


class ActiveScopeUpdateRequest(BaseModel):
    active_campaign_kind: str = Field(min_length=1, max_length=16)
    reason: str = Field(min_length=3, max_length=2000)


class PromocodeCreateRequest(BaseModel):
    customer_erp_id: str = Field(min_length=1, max_length=64)
    promocode: str = Field(min_length=8, max_length=20)
    reason: str = Field(min_length=3, max_length=2000)
    campaign_id: str | None = None
    customer_card: str | None = Field(default=None, max_length=64)
    customer_name: str | None = Field(default=None, max_length=128)
    customer_phone: str | None = Field(default=None, max_length=32)
    expires_at: datetime | None = None
    status: str | None = None


class PromocodePatchRequest(BaseModel):
    status: str | None = None
    expires_at: datetime | None = None
    campaign_id: str | None = None
    customer_erp_id: str | None = Field(default=None, min_length=1, max_length=64)
    promocode: str | None = Field(default=None, min_length=8, max_length=20)
    customer_card: str | None = Field(default=None, max_length=64)
    customer_name: str | None = Field(default=None, max_length=128)
    customer_phone: str | None = Field(default=None, max_length=32)
    clear_campaign: bool = False
    reason: str = Field(min_length=3, max_length=2000)


class PromocodeDeleteRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class PromocodeDetailResponse(BaseModel):
    id: str
    customer_erp_id: str
    promocode: str
    status: str
    campaign_id: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    campaign_kind: str | None = None
    customer_card: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    created_at: str
    expires_at: str
    redeemed_at: str | None = None


class PromocodeCreateDefaultsResponse(BaseModel):
    active_campaign_kind: str
    default_campaign_id: str | None = None
    status: str = "ACTIVE"
    expires_at: str
    promocode_ttl_days: int
    campaigns: list[CampaignSummary] = []


class AdminMutationResponse(BaseModel):
    ok: bool = True
    entity: str
    entity_id: str
    audit_log_id: int | None = None


class AdminTableName(StrEnum):
    PROMOCODES = "promocodes"
    CAMPAIGNS = "campaigns"
    CHECKER_LOGS = "checker_logs"
    FRAUD_WARNINGS = "fraud_warnings"
    SALE_OBSERVATIONS = "sale_observations"
    ADMIN_AUDIT_LOGS = "admin_audit_logs"
    TELEGRAM_NOTIFICATION_LOGS = "telegram_notification_logs"
