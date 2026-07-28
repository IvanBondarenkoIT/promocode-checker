"""Run Alembic migrations against the configured DATABASE_URL."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
REQUIRED_TABLES = ("promocodes", "checker_logs", "fraud_warnings")


def _load_database_url() -> str:
    sys.path.insert(0, str(BACKEND_DIR))
    from app.core.config import get_settings

    return get_settings().database_url


def _schema_ready(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        return all(table in tables for table in REQUIRED_TABLES)
    finally:
        engine.dispose()


def _run_alembic(*args: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        check=False,
    )
    return result.returncode


def _reset_alembic_stamp(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM alembic_version"))
    finally:
        engine.dispose()


def main() -> int:
    database_url = _load_database_url()

    if _run_alembic("upgrade", "head") != 0:
        return 1

    if _schema_ready(database_url):
        return 0

    # Recover from a stamped-but-empty DB (alembic_version without tables).
    print(
        "Migration stamp found but core tables are missing; "
        "resetting alembic_version and re-applying schema.",
        file=sys.stderr,
    )
    _reset_alembic_stamp(database_url)
    if _run_alembic("upgrade", "head") != 0:
        return 1
    if not _schema_ready(database_url):
        print("Schema is still incomplete after re-apply.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
