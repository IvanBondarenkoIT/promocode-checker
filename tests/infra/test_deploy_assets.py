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


def test_dockerignore_allows_coffee_whitelist() -> None:
    """Dockerfile copies docs/coffee-beans-whitelist.txt; docs/ must not hide it."""
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert (
        "docs/coffee-beans-whitelist.txt" in ignore
        or "!docs/coffee-beans-whitelist.txt" in ignore
    )
    assert (ROOT / "docs" / "coffee-beans-whitelist.txt").is_file()


def test_compose_files_define_healthchecks() -> None:
    app_compose = (ROOT / "infra" / "docker-compose.app.yml").read_text(encoding="utf-8")
    prod_compose = (ROOT / "infra" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "healthcheck:" in app_compose
    assert "healthcheck:" in prod_compose
    assert "restart:" in prod_compose


def test_prod_compose_has_host_gateway_for_firebird() -> None:
    prod_compose = (ROOT / "infra" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "host.docker.internal:host-gateway" in prod_compose
    assert "ERP_ACCESS_MODE: ${ERP_ACCESS_MODE:-direct}" in prod_compose


def test_prod_compose_health_endpoint() -> None:
    prod_compose = (ROOT / "infra" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "/health" in prod_compose


def test_prod_env_example_has_required_keys() -> None:
    example = ROOT / "infra" / ".env.prod.example"
    content = example.read_text(encoding="utf-8")
    for key in ("POSTGRES_PASSWORD", "APP_SECRET_KEY", "ADMIN_PASSWORD", "ERP_ACCESS_MODE", "FIREBIRD_DSN"):
        assert key in content


def test_compose_app_example_config_json() -> None:
    payload = json.loads((ROOT / "desktop" / "config.example.json").read_text(encoding="utf-8"))
    assert payload["cashierBaseUrl"].startswith("http")
