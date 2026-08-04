"""Hourly reconcile + frequent Telegram bot poll for Docker worker."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVAL_SECONDS = 3600
BOT_POLL_SECONDS = 5


def main() -> int:
    python = sys.executable
    reconcile = ROOT / "scripts" / "run_reconcile.py"
    bot_poll = ROOT / "scripts" / "run_telegram_bot_poll.py"
    print(
        f"reconcile worker started; reconcile_interval={INTERVAL_SECONDS}s "
        f"bot_poll={BOT_POLL_SECONDS}s",
        flush=True,
    )
    next_reconcile = 0.0
    while True:
        now = time.monotonic()
        if now >= next_reconcile:
            result = subprocess.run([python, str(reconcile)], check=False)
            if result.returncode != 0:
                print(f"reconcile exit code {result.returncode}", flush=True)
            next_reconcile = time.monotonic() + INTERVAL_SECONDS

        poll = subprocess.run([python, str(bot_poll)], check=False)
        if poll.returncode != 0:
            print(f"bot poll exit code {poll.returncode}", flush=True)
        time.sleep(BOT_POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
