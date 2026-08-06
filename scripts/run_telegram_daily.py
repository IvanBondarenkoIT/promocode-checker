"""Run Telegram daily digest tick (day-start / EOD)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.jobs.telegram_daily import run_telegram_daily  # noqa: E402


def main() -> int:
    with SessionLocal() as db:
        result = run_telegram_daily(db)
        db.commit()
    bits = []
    if result.day_start_sent:
        bits.append("day_start")
    if result.eod_sent:
        bits.append("eod")
    if result.errors:
        bits.append(f"errors={len(result.errors)}")
    print("telegram_daily: " + (",".join(bits) if bits else "noop"), flush=True)
    return 1 if result.errors and not (result.day_start_sent or result.eod_sent) else 0


if __name__ == "__main__":
    raise SystemExit(main())
