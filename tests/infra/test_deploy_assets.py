"""Deploy asset and config smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_exists_and_builds_frontend() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "frontend-build" in text
    assert "docker-entrypoint.sh" in text
    assert "/app/static" in text


def test_compose_files_define_healthchecks() -> None:
    app_compose = (ROOT / "infra" / "docker-compose.app.yml").read_text(encoding="utf-8")
    prod_compose = (ROOT / "infra" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "healthcheck:" in app_compose
    assert "healthcheck:" in prod_compose
    assert "restart:" in prod_compose


def test_railway_config_present() -> None:
    railway = ROOT / "railway.toml"
    assert railway.is_file()
    assert "/health" in railway.read_text(encoding="utf-8")


def test_prod_env_example_has_required_keys() -> None:
    example = ROOT / "infra" / ".env.prod.example"
    content = example.read_text(encoding="utf-8")
    for key in ("POSTGRES_PASSWORD", "APP_SECRET_KEY", "ADMIN_PASSWORD"):
        assert key in content


def test_compose_app_example_config_json() -> None:
    payload = json.loads((ROOT / "desktop" / "config.example.json").read_text(encoding="utf-8"))
    assert payload["cashierBaseUrl"].startswith("http")
