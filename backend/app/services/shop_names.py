"""Shop display names for Telegram (point_id → label)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHOP_NAMES_PATH = ROOT / "config" / "shop_names.json"


@lru_cache
def _load_shop_names() -> dict[str, str]:
    if not SHOP_NAMES_PATH.is_file():
        return {}
    try:
        raw = json.loads(SHOP_NAMES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    mapping = raw.get("shops") if isinstance(raw, dict) else raw
    if not isinstance(mapping, dict):
        return {}
    return {str(k): str(v) for k, v in mapping.items()}


def shop_label(point_id: str | None) -> str:
    pid = (point_id or "").strip() or "—"
    return _load_shop_names().get(pid, pid)
