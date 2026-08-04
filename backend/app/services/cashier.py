from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models import CheckerActionType, CheckerLog, Promocode, PromocodeStatus
from app.schemas.cashier import CashierCodeResponse, CashierResult
from app.services.promocode_close import close_promocode, lock_promocode_by_code
from app.services.promocode_generator import is_valid_promocode
from app.services.telegram import send_alert
from app.services.telegram_messages import msg_manual_close, msg_scan


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
    campaign = promocode.campaign if promocode is not None else None
    return CashierCodeResponse(
        result=result,
        code=code,
        point_id=point_id,
        status=promocode.status.value if promocode is not None else None,
        expires_at=promocode.expires_at if promocode is not None else None,
        redeemed_at=promocode.redeemed_at if promocode is not None else None,
        log_id=log_id,
        campaign_code=campaign.code if campaign is not None else None,
        campaign_name=campaign.name if campaign is not None else None,
        campaign_ends_at=campaign.ends_at if campaign is not None else None,
    )


def _get_promocode(db: Session, code: str) -> Promocode | None:
    return db.scalar(
        select(Promocode)
        .options(joinedload(Promocode.campaign))
        .where(Promocode.promocode == code)
    )


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
    response = _build_response(
        result=result,
        code=code,
        point_id=point_id,
        promocode=promocode,
        log_id=log.id,
    )
    _notify_scan(db, response=response, promocode=promocode, when=log.scan_time)
    return response


def redeem_promocode(db: Session, *, code: str, point_id: str) -> CashierCodeResponse:
    if not is_valid_promocode(code):
        return _build_response(
            result=CashierResult.INVALID_FORMAT,
            code=code,
            point_id=point_id,
        )

    promocode = lock_promocode_by_code(db, code)
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
    response = _build_response(
        result=CashierResult.REDEEMED,
        code=code,
        point_id=point_id,
        promocode=promocode,
        log_id=log.id,
    )
    _notify_manual_close(db, promocode=promocode, point_id=point_id, when=log.scan_time)
    return response


def _status_label(result: CashierResult) -> str:
    mapping = {
        CashierResult.VALID: "ACTIVE",
        CashierResult.USED: "USED",
        CashierResult.EXPIRED: "EXPIRED",
        CashierResult.NOT_FOUND: "NOT FOUND",
        CashierResult.REDEEMED: "APPLIED",
        CashierResult.INVALID_FORMAT: "INVALID",
    }
    return mapping.get(result, result.value)


def _notify_scan(
    db: Session,
    *,
    response: CashierCodeResponse,
    promocode: Promocode | None,
    when: datetime,
) -> None:
    settings = get_settings()
    send_alert(
        db,
        event_type="cashier_scan",
        dedup_key=f"scan:{response.code}:{response.point_id}:{when.isoformat()}",
        message=msg_scan(
            code=response.code,
            status_label=_status_label(response.result),
            point_id=response.point_id,
            when=when,
            customer_erp_id=promocode.customer_erp_id if promocode else None,
            campaign_name=response.campaign_name,
            tz_name=settings.app_timezone,
        ),
        settings=settings,
    )


def _notify_manual_close(
    db: Session,
    *,
    promocode: Promocode,
    point_id: str,
    when: datetime,
) -> None:
    settings = get_settings()
    send_alert(
        db,
        event_type="cashier_manual_close",
        dedup_key=f"manual_close:{promocode.promocode}:{when.isoformat()}",
        message=msg_manual_close(
            code=promocode.promocode,
            point_id=point_id,
            when=when,
            customer_erp_id=promocode.customer_erp_id,
            fraud_window_hours=settings.fraud_match_window_hours,
            tz_name=settings.app_timezone,
        ),
        settings=settings,
    )
