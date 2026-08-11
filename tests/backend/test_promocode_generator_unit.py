from app.services.promocode_generator import (
    PROMOCODE_MAX_LENGTH,
    PROMOCODE_MIN_LENGTH,
    is_valid_promocode,
)


def test_is_valid_promocode_accepts_8_to_20_digits() -> None:
    assert is_valid_promocode("12345678") is True
    assert is_valid_promocode("2200000109743") is True
    assert is_valid_promocode("1" * PROMOCODE_MAX_LENGTH) is True
    assert is_valid_promocode("1234567") is False
    assert is_valid_promocode("1" * (PROMOCODE_MAX_LENGTH + 1)) is False
    assert is_valid_promocode("1234abcd") is False
    assert PROMOCODE_MIN_LENGTH == 8
