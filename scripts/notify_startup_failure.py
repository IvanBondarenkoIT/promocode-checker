"""Send Telegram alert when the app container fails during startup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.telegram import send_alert  # noqa: E402


def main() -> int:
    message = " ".join(sys.argv[1:]).strip() or "Promocode checker startup failure"
    settings = get_settings()
    try:
        with SessionLocal() as db:
            send_alert(
                db,
                event_type="app_crash",
                dedup_key="app_crash:startup",
                message=f"[startup] {message}",
                settings=settings,
                topic="system",
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"startup alert skipped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
