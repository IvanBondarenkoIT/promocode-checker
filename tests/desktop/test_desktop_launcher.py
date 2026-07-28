"""Desktop wrapper config and launcher checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "desktop"
EXAMPLE_CONFIG = DESKTOP / "config.example.json"
LAUNCHER = DESKTOP / "launch-cashier.ps1"

REQUIRED_KEYS = {"cashierBaseUrl", "pointId", "fullscreen", "browser"}


def test_example_config_is_valid_json_with_required_keys() -> None:
    payload = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS.issubset(payload.keys())
    assert payload["browser"] in {"auto", "edge", "chrome"}
    assert re.match(r"^https?://", payload["cashierBaseUrl"])
    assert payload["pointId"].strip()


def test_launch_script_exists_and_references_config() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "config.json" in text
    assert "--app=" in text
    assert "point_id" in text
