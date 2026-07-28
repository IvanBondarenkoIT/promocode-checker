import pytest
from app.models import (
    AdminAuditLog,
    CheckerLog,
    FraudWarning,
    Promocode,
    TelegramNotificationLog,
)
from sqlalchemy import inspect

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def test_core_tables_exist(engine) -> None:
    table_names = set(inspect(engine).get_table_names())
    assert {
        "promocodes",
        "checker_logs",
        "fraud_warnings",
        "admin_audit_logs",
        "telegram_notification_logs",
    }.issubset(table_names)


def test_promocode_unique_constraint(db_session) -> None:
    promocode_indexes = {
        index["name"] for index in inspect(db_session.bind).get_indexes("promocodes")
    }
    assert "ix_promocodes_promocode" in promocode_indexes


def test_checker_log_foreign_key_to_promocode(db_session) -> None:
    foreign_keys = inspect(db_session.bind).get_foreign_keys("checker_logs")
    assert any(fk["referred_table"] == "promocodes" for fk in foreign_keys)


def test_admin_audit_and_telegram_models_are_mappable() -> None:
    assert AdminAuditLog.__tablename__ == "admin_audit_logs"
    assert TelegramNotificationLog.__tablename__ == "telegram_notification_logs"
    assert FraudWarning.__tablename__ == "fraud_warnings"
    assert CheckerLog.__tablename__ == "checker_logs"
    assert Promocode.__tablename__ == "promocodes"
