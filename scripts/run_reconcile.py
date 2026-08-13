"""Run one ERP reconcile pass (worker loop / Task Scheduler)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.jobs.reconcile import run_reconcile  # noqa: E402


def main() -> int:
    settings = get_settings()
    with SessionLocal() as db:
        try:
            result = run_reconcile(db, settings=settings)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"reconcile failed: {exc}", file=sys.stderr)
            return 1

    print(
        "reconcile ok "
        f"auto_closed={len(result.auto_closed)} "
        f"fraud_warnings={len(result.fraud_warnings)} "
        f"observed={len(result.observed)} "
        f"erp_rows={result.erp_rows} "
        f"erp_ms={result.erp_ms}"
    )
    if result.auto_closed:
        print("auto_closed:", ", ".join(result.auto_closed))
    if result.fraud_warnings:
        print("fraud_warnings:", ", ".join(result.fraud_warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
