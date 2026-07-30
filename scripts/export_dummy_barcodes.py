"""Export Code128 PNG images for dummy promocodes (local / server tryouts)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.services.barcode import render_code128_png  # noqa: E402
from seed_promocodes import DUMMY_PROMOCODES  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Write dummy promocode barcode PNGs.")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "dummy-barcodes",
        help="Output directory for PNG files",
    )
    args = parser.parse_args()
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for item in DUMMY_PROMOCODES:
        path = out_dir / f"{item.promocode}.png"
        path.write_bytes(render_code128_png(item.promocode))
        written.append(path)

    print(f"Wrote {len(written)} barcode PNG(s) to {out_dir.resolve()}")
    for path in written:
        print(path.name)


if __name__ == "__main__":
    main()
