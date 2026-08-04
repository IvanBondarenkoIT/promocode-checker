"""Send DEMO pack of all Telegram message types to subscribers.

  python scripts/send_telegram_message_samples.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.telegram_bot import send_demo_to_all_subscribers  # noqa: E402
from app.services.telegram_subscribers import list_recipient_chat_ids  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not (settings.telegram_bot_token or "").strip():
        print("TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        recipients = list_recipient_chat_ids(db, settings)
        if not recipients:
            print(
                "No recipients. Subscribe via bot (promo) or set TELEGRAM_ALERT_CHAT_ID.",
                file=sys.stderr,
            )
            return 2
        count = send_demo_to_all_subscribers(db, settings=settings)
        db.commit()
        print(f"Sent {count} DEMO messages to {len(recipients)} recipient(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
