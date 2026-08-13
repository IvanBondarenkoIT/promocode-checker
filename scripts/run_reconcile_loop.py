"""Hourly reconcile + frequent Telegram bot poll + daily digest tick."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTERVAL_SECONDS = 600
BOT_POLL_SECONDS = 5


def _reconcile_interval() -> int:
    raw = os.getenv("RECONCILE_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS
    return max(60, value)


def main() -> int:
    python = sys.executable
    reconcile = ROOT / "scripts" / "run_reconcile.py"
    bot_poll = ROOT / "scripts" / "run_telegram_bot_poll.py"
    daily = ROOT / "scripts" / "run_telegram_daily.py"
    interval = _reconcile_interval()
    print(
        f"reconcile worker started; reconcile_interval={interval}s "
        f"bot_poll={BOT_POLL_SECONDS}s daily_tick=each_loop",
        flush=True,
    )
    next_reconcile = 0.0
    while True:
        now = time.monotonic()
        if now >= next_reconcile:
            result = subprocess.run([python, str(reconcile)], check=False)
            if result.returncode != 0:
                print(f"reconcile exit code {result.returncode}", flush=True)
            next_reconcile = time.monotonic() + interval

        poll = subprocess.run([python, str(bot_poll)], check=False)
        if poll.returncode != 0:
            print(f"bot poll exit code {poll.returncode}", flush=True)

        daily_run = subprocess.run([python, str(daily)], check=False)
        if daily_run.returncode != 0:
            print(f"telegram_daily exit code {daily_run.returncode}", flush=True)

        time.sleep(BOT_POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
