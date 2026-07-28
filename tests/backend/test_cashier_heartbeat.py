import pytest
from fastapi.testclient import TestClient

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def test_heartbeat_returns_point_and_server_time(client: TestClient) -> None:
    response = client.post("/api/v1/cashier/heartbeat", json={"point_id": "shop_heartbeat"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["point_id"] == "shop_heartbeat"
    assert payload["server_time"]
