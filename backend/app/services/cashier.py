from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus
from app.schemas.cashier import CashierCodeResponse, CashierResult
from app.services.promocode_close import close_promocode
from app.services.promocode_generator import is_valid_promocode


def _now() -> datetime:
    return datetime.now(UTC)


def _is_expired(promocode: Promocode, *, now: datetime | None = None) -> bool:
    current = now or _now()
    expires_at = promocode.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= current


def _resolve_lookup_result(promocode: Promocode | None) -> CashierResult:
    if promocode is None:
        return CashierResult.NOT_FOUND
    if promocode.status == PromocodeStatus.USED:
        return CashierResult.USED
    if _is_expired(promocode):
        return CashierResult.EXPIRED
    return CashierResult.VALID


def _build_response(
    *,
    result: CashierResult,
    code: str,
    point_id: str,
    promocode: Promocode | None = None,
    log_id: int | None = None,
) -> CashierCodeResponse:
    return CashierCodeResponse(
        result=result,
        code=code,
        point_id=point_id,
        status=promocode.status.value if promocode is not None else None,
        expires_at=promocode.expires_at if promocode is not None else None,
        redeemed_at=promocode.redeemed_at if promocode is not None else None,
        log_id=log_id,
    )


def _get_promocode(db: Session, code: str) -> Promocode | None:
    return db.scalar(select(Promocode).where(Promocode.promocode == code))


def _write_log(
    db: Session,
    *,
    scanned_code: str,
    action_type: CheckerActionType,
    point_id: str,
    promocode_id,
) -> CheckerLog:
    log = CheckerLog(
        promocode_id=promocode_id,
        scanned_code=scanned_code,
        action_type=action_type,
        point_id=point_id,
        erp_sale_matched=False,
    )
    db.add(log)
    db.flush()
    return log


def check_promocode(db: Session, *, code: str, point_id: str) -> CashierCodeResponse:
    if not is_valid_promocode(code):
        return _build_response(
            result=CashierResult.INVALID_FORMAT,
            code=code,
            point_id=point_id,
        )

    promocode = _get_promocode(db, code)
    result = _resolve_lookup_result(promocode)
    log = _write_log(
        db,
        scanned_code=code,
        action_type=CheckerActionType.SCAN_CHECK,
        point_id=point_id,
        promocode_id=promocode.id if promocode is not None else None,
    )
    return _build_response(
        result=result,
        code=code,
        point_id=point_id,
        promocode=promocode,
        log_id=log.id,
    )


def redeem_promocode(db: Session, *, code: str, point_id: str) -> CashierCodeResponse:
    if not is_valid_promocode(code):
        return _build_response(
            result=CashierResult.INVALID_FORMAT,
            code=code,
            point_id=point_id,
        )

    promocode = _get_promocode(db, code)
    lookup_result = _resolve_lookup_result(promocode)
    if lookup_result != CashierResult.VALID:
        return _build_response(
            result=lookup_result,
            code=code,
            point_id=point_id,
            promocode=promocode,
        )

    assert promocode is not None
    log = close_promocode(
        db,
        promocode,
        action_type=CheckerActionType.MANUAL_CLOSE,
        point_id=point_id,
        erp_sale_matched=False,
    )
    return _build_response(
        result=CashierResult.REDEEMED,
        code=code,
        point_id=point_id,
        promocode=promocode,
        log_id=log.id,
    )
