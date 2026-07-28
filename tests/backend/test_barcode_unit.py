import pytest
from app.services.barcode import render_code128_png


def test_render_code128_png_returns_png_bytes() -> None:
    png = render_code128_png("12345678")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_code128_png_rejects_invalid_code() -> None:
    with pytest.raises(ValueError, match="8 digits"):
        render_code128_png("123")
