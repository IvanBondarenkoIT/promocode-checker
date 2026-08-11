from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.cashier import CashierCodeRequest, CashierCodeResponse
from app.services.barcode import render_code128_png
from app.services.cashier import check_promocode, redeem_promocode
from app.services.promocode_generator import is_valid_promocode

router = APIRouter(prefix="/cashier", tags=["cashier"])

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


class HeartbeatRequest(BaseModel):
    point_id: str | None = Field(default=None, max_length=64)


class HeartbeatResponse(BaseModel):
    ok: bool = True
    point_id: str
    server_time: datetime


def _resolve_point_id(point_id: str | None, settings: Settings) -> str:
    return point_id or settings.default_point_id


@router.post("/check", response_model=CashierCodeResponse)
def check_code(
    payload: CashierCodeRequest,
    db: DbSession,
    settings: AppSettings,
) -> CashierCodeResponse:
    return check_promocode(
        db,
        code=payload.code,
        point_id=_resolve_point_id(payload.point_id, settings),
    )


@router.post("/redeem", response_model=CashierCodeResponse)
def redeem_code(
    payload: CashierCodeRequest,
    db: DbSession,
    settings: AppSettings,
) -> CashierCodeResponse:
    return redeem_promocode(
        db,
        code=payload.code,
        point_id=_resolve_point_id(payload.point_id, settings),
    )


@router.post("/heartbeat", response_model=HeartbeatResponse)
def heartbeat(payload: HeartbeatRequest, settings: AppSettings) -> HeartbeatResponse:
    return HeartbeatResponse(
        ok=True,
        point_id=_resolve_point_id(payload.point_id, settings),
        server_time=datetime.now(UTC),
    )


@router.get("/barcode/{code}")
def barcode_image(code: str) -> Response:
    if not is_valid_promocode(code):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Promocode must be 8-20 digits",
        )
    png = render_code128_png(code)
    return Response(content=png, media_type="image/png")
