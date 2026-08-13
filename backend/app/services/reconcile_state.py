"""ERP observe window: persistent cursor minus overlap, floored to local day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.reconcile_state import RECONCILE_STATE_ID, ReconcileState

MIN_OVERLAP_HOURS = 1


@dataclass(frozen=True)
class ReconcileWindow:
    since: datetime
    until: datetime
    used_cursor: bool


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def zoneinfo_or_utc(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except Exception:  # noqa: BLE001 — bad tz must not break reconcile
        return ZoneInfo("UTC")


def local_date(value: datetime, tz_name: str) -> date:
    """Calendar date in app timezone (ERP DAT_ has no clock time)."""
    return ensure_aware(value).astimezone(zoneinfo_or_utc(tz_name)).date()


def start_of_local_day(value: datetime, tz_name: str) -> datetime:
    """UTC instant of local midnight for the calendar day of ``value``."""
    tz = zoneinfo_or_utc(tz_name)
    local = ensure_aware(value).astimezone(tz)
    midnight = datetime.combine(local.date(), time.min, tzinfo=tz)
    return midnight.astimezone(UTC)


def compute_observe_window(
    *,
    now: datetime,
    earliest_created: datetime,
    last_scan_until: datetime | None,
    overlap_hours: int,
    tz_name: str,
) -> ReconcileWindow:
    """Return ERP [since, until].

    First run uses the oldest active code (floored to local midnight).
    Later runs use ``last_scan_until - overlap``, still not before that floor.
    Flooring to local day keeps date-only ``S.DAT_`` (midnight) inside the SQL
    window so same-day sales are not dropped at the seam.
    """
    until = ensure_aware(now)
    floor = ensure_aware(earliest_created)
    hours = max(MIN_OVERLAP_HOURS, int(overlap_hours))
    if last_scan_until is None:
        raw_since = floor
        used_cursor = False
    else:
        raw_since = max(floor, ensure_aware(last_scan_until) - timedelta(hours=hours))
        used_cursor = True
    since = start_of_local_day(raw_since, tz_name)
    if since > until:
        since = start_of_local_day(until, tz_name)
    return ReconcileWindow(since=since, until=until, used_cursor=used_cursor)


def get_reconcile_state(db: Session) -> ReconcileState:
    row = db.get(ReconcileState, RECONCILE_STATE_ID)
    if row is None:
        row = ReconcileState(id=RECONCILE_STATE_ID)
        db.add(row)
        db.flush()
    return row


def record_observe_scan(
    db: Session,
    *,
    scan_until: datetime,
    run_at: datetime,
    erp_rows: int,
    erp_ms: int,
) -> ReconcileState:
    row = get_reconcile_state(db)
    row.last_scan_until = ensure_aware(scan_until)
    row.last_run_at = ensure_aware(run_at)
    row.last_erp_rows = erp_rows
    row.last_erp_ms = erp_ms
    row.updated_at = ensure_aware(run_at)
    db.flush()
    return row
