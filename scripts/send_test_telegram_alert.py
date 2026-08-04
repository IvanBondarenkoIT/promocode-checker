"""Send one test Telegram alert using TELEGRAM_* from env.

Usage:
  python scripts/send_test_telegram_alert.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.telegram import send_alert  # noqa: E402


def main() -> int:
    settings = get_settings()
    token = (settings.telegram_bot_token or "").strip()
    chat_id = (settings.telegram_alert_chat_id or "").strip()
    if not token or not chat_id:
        print(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID must be set "
            "(see docs/runbooks/telegram-alerts.md)",
            file=sys.stderr,
        )
        return 1

    with SessionLocal() as db:
        log = send_alert(
            db,
            event_type="ops_smoke_test",
            dedup_key=f"ops_smoke_test:{uuid4()}",
            message="promocode-checker Telegram smoke test OK",
            settings=settings,
        )
        db.commit()
        print(f"delivery_status={log.delivery_status} chat_id={log.chat_id}")
        if log.delivery_status != "sent":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
