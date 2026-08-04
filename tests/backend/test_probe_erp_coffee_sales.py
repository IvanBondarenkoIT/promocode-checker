"""Tests for scripts/probe_erp_coffee_sales.py helpers (mock path)."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_erp_coffee_sales as probe  # noqa: E402


def test_load_shop_cards_dedupes(tmp_path: Path) -> None:
    path = tmp_path / "cards.json"
    path.write_text(
        json.dumps(
            {
                "cards": [
                    {"id": "12523", "name": "A"},
                    {"id": "12523", "name": "dup"},
                    {"id": "21470", "name": "B"},
                ]
            }
        ),
        encoding="utf-8",
    )
    cards = probe.load_shop_cards(path)
    assert [c["id"] for c in cards] == ["12523", "21470"]


def test_mock_probe_writes_csv_json(tmp_path: Path) -> None:
    cards = [
        {"id": "12523", "name": "КЛИЕНТ PALIASHVILI"},
        {"id": "21470", "name": "КЛИЕНТ DK BATUMI"},
    ]
    day = date(2026, 8, 4)
    matches = probe.mock_sales_for_day(day, cards)
    assert len(matches) == 2
    csv_path, json_path = probe.write_outputs(
        out_dir=tmp_path,
        day=day,
        matches=matches,
        name_by_id={c["id"]: c["name"] for c in cards},
    )
    assert csv_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["day"] == "2026-08-04"
    assert payload["count"] == 2
    assert payload["rows"][0]["customer_erp_id"] == "12523"
