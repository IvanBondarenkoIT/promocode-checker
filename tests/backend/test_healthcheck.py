from unittest.mock import MagicMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.main.SessionLocal")
def test_healthcheck_returns_ok_when_database_is_available(mock_session_local: MagicMock) -> None:
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = False
    mock_session_local.return_value = mock_session

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["schema"] == "ok"


@patch("app.main.SessionLocal")
def test_healthcheck_reports_missing_schema(mock_session_local: MagicMock) -> None:
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = False
    mock_session_local.return_value = mock_session

    from sqlalchemy.exc import ProgrammingError

    mock_session.execute.side_effect = [
        None,
        ProgrammingError("SELECT 1 FROM promocodes", {}, Exception("missing")),
    ]

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "ok"
    assert payload["schema"] == "missing"
