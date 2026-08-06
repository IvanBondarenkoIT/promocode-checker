from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CashierResult(StrEnum):
    VALID = "valid"
    REDEEMED = "redeemed"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    USED = "used"
    INVALID_FORMAT = "invalid_format"
    OUT_OF_SCOPE = "out_of_scope"


class CashierCodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    point_id: str | None = Field(default=None, max_length=64)


class CashierCodeResponse(BaseModel):
    result: CashierResult
    code: str
    point_id: str
    status: str | None = None
    expires_at: datetime | None = None
    redeemed_at: datetime | None = None
    log_id: int | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    campaign_ends_at: datetime | None = None
    campaign_kind: str | None = None
    active_campaign_kind: str | None = None
