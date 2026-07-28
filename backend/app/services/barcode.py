from io import BytesIO

from barcode import Code128
from barcode.writer import ImageWriter

from app.services.promocode_generator import is_valid_promocode


def render_code128_png(code: str) -> bytes:
    if not is_valid_promocode(code):
        raise ValueError("Promocode must be exactly 8 digits")

    buffer = BytesIO()
    Code128(code, writer=ImageWriter()).write(
        buffer,
        options={
            "module_height": 12.0,
            "quiet_zone": 2.0,
            "write_text": True,
            "font_size": 10,
            "text_distance": 4.0,
        },
    )
    return buffer.getvalue()
