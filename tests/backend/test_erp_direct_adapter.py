"""Unit tests for DirectErpAdapter and ERP factory fallback wiring."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from app.core.config import Settings
from app.integrations.erp.base import ErpError
from app.integrations.erp.direct import DirectErpAdapter
from app.integrations.erp.factory import FallbackErpAdapter, get_erp_adapter
from app.integrations.erp.types import CoffeeSaleMatch


def _settings(**overrides: object) -> Settings:
    base = {
        "ERP_ACCESS_MODE": "direct",
        "FIREBIRD_DSN": "localhost/3055:DK_GEORGIA",
        "FIREBIRD_USER": "api_readonly",
        "FIREBIRD_PASSWORD": "secret",
        "FIREBIRD_LIBRARY_PATH": "",
        "PROXY_API_URL": "http://proxy.test:8010",
        "PROXY_API_TOKEN": "token",
    }
    base.update(overrides)
    return Settings(**base)


def test_direct_adapter_requires_dsn() -> None:
    with pytest.raises(ErpError, match="FIREBIRD_DSN"):
        DirectErpAdapter(_settings(FIREBIRD_DSN=""))


def test_direct_adapter_passes_fb_library_name(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeCursor:
        description = [("CUSTOMER_ERP_ID",)]

        def execute(self, query: str, params: tuple[object, ...]) -> None:
            captured["query"] = query
            captured["params"] = params

        def fetchall(self) -> list[tuple[str]]:
            return []

        def close(self) -> None:
            pass

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

        def close(self) -> None:
            pass

    def fake_connect(**kwargs: object) -> FakeConnection:
        captured["connect_kwargs"] = kwargs
        return FakeConnection()

    fake_fdb = ModuleType("fdb")
    fake_fdb.connect = fake_connect  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fdb", fake_fdb)

    adapter = DirectErpAdapter(
        _settings(FIREBIRD_LIBRARY_PATH=r"C:\tools\fbembed.dll"),
    )
    since = datetime(2026, 8, 1, tzinfo=UTC)
    until = datetime(2026, 8, 2, tzinfo=UTC)
    adapter.find_coffee_sales(["21470"], since=since, until=until)

    connect_kwargs = captured["connect_kwargs"]
    assert connect_kwargs["fb_library_name"] == r"C:\tools\fbembed.dll"
    assert connect_kwargs["dsn"] == "localhost/3055:DK_GEORGIA"
    assert connect_kwargs["user"] == "api_readonly"


def test_direct_connect_error_includes_dsn_and_user(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_connect(**kwargs: object) -> None:
        raise OSError("Connection refused")

    fake_fdb = ModuleType("fdb")
    fake_fdb.connect = fake_connect  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fdb", fake_fdb)

    adapter = DirectErpAdapter(_settings())
    since = datetime(2026, 8, 1, tzinfo=UTC)
    until = datetime(2026, 8, 2, tzinfo=UTC)
    with pytest.raises(ErpError, match="dsn=localhost/3055:DK_GEORGIA"):
        adapter.find_coffee_sales(["21470"], since=since, until=until)


def test_direct_server_version(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCursor:
        description = [("RDB$GET_CONTEXT",)]

        def execute(self, query: str, params: tuple[object, ...]) -> None:
            pass

        def fetchall(self) -> list[tuple[str]]:
            return [("WI-V2.5.9.27139",)]

        def close(self) -> None:
            pass

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

        def close(self) -> None:
            pass

    fake_fdb = ModuleType("fdb")
    fake_fdb.connect = lambda **kwargs: FakeConnection()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fdb", fake_fdb)

    adapter = DirectErpAdapter(_settings())
    assert "2.5.9" in adapter.server_version()


def test_fallback_direct_to_proxy() -> None:
    primary = MagicMock()
    primary.find_coffee_sales.side_effect = ErpError("direct down")
    fallback = MagicMock()
    expected = [
        CoffeeSaleMatch(
            customer_erp_id="21470",
            sold_at=datetime(2026, 8, 1, tzinfo=UTC),
            group_id=11077,
            product_name="Coffee",
        )
    ]
    fallback.find_coffee_sales.return_value = expected

    adapter = FallbackErpAdapter(primary, fallback)
    since = datetime(2026, 8, 1, tzinfo=UTC)
    until = datetime(2026, 8, 2, tzinfo=UTC)
    result = adapter.find_coffee_sales(["21470"], since=since, until=until)
    assert result == expected
    fallback.find_coffee_sales.assert_called_once()


def test_get_erp_adapter_direct_wraps_proxy_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.integrations.erp.factory.DirectErpAdapter",
        lambda cfg: MagicMock(name="direct"),
    )
    monkeypatch.setattr(
        "app.integrations.erp.factory.ProxyErpAdapter",
        lambda cfg: MagicMock(name="proxy"),
    )
    adapter = get_erp_adapter(_settings(ERP_ACCESS_MODE="direct"))
    assert isinstance(adapter, FallbackErpAdapter)


def test_get_erp_adapter_direct_without_proxy_token_has_no_fallback() -> None:
    adapter = get_erp_adapter(
        _settings(ERP_ACCESS_MODE="direct", PROXY_API_TOKEN=""),
    )
    assert isinstance(adapter, FallbackErpAdapter)
    assert adapter._fallback is None  # noqa: SLF001
