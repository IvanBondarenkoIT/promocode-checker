from datetime import UTC, datetime, timedelta

from app.services.promocode_generator import calculate_expires_at, is_valid_promocode


def test_is_valid_promocode_accepts_exactly_8_digits() -> None:
    assert is_valid_promocode("12345678") is True
    assert is_valid_promocode("1234567") is False
    assert is_valid_promocode("123456789") is False
    assert is_valid_promocode("1234abcd") is False


def test_calculate_expires_at_uses_ttl_days() -> None:
    created_at = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    expires_at = calculate_expires_at(created_at, ttl_days=30)
    assert expires_at == created_at + timedelta(days=30)
