"""Hourly reconcile loop for Docker worker service."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVAL_SECONDS = 3600


def main() -> int:
    python = sys.executable
    reconcile = ROOT / "scripts" / "run_reconcile.py"
    print(f"reconcile worker started; interval={INTERVAL_SECONDS}s", flush=True)
    while True:
        result = subprocess.run([python, str(reconcile)], check=False)
        if result.returncode != 0:
            print(f"reconcile exit code {result.returncode}", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
