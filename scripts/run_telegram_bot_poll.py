"""Poll Telegram bot once (or loop) for subscribe / demo commands.

Examples:
  python scripts/run_telegram_bot_poll.py
  python scripts/run_telegram_bot_poll.py --loop --timeout 25
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.telegram_bot import process_bot_updates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll Telegram bot updates")
    parser.add_argument("--loop", action="store_true", help="Poll forever")
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Long-poll timeout seconds (0 = short)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Sleep between polls when --loop and timeout=0",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not (settings.telegram_bot_token or "").strip():
        print("TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
        return 1

    print(
        f"Bot poll ready keyword={settings.telegram_subscribe_keyword!r} "
        f"loop={args.loop}",
        flush=True,
    )

    while True:
        with SessionLocal() as db:
            handled = process_bot_updates(
                db, settings=settings, timeout=args.timeout
            )
            db.commit()
        if handled:
            print(f"handled={handled}", flush=True)
        if not args.loop:
            break
        if args.timeout <= 0:
            time.sleep(max(0.5, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
