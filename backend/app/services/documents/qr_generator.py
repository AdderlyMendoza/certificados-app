"""Generación de códigos QR configurables."""
from __future__ import annotations

import io

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

from app.schemas.template import QRConfig

_ECC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def generate_qr_png(content: str, config: QRConfig) -> bytes:
    """Genera un PNG (bytes) del QR según la configuración dada."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=_ECC_MAP[config.error_correction],
        box_size=10,
        border=config.margin,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(fill_color=config.fill_color, back_color=config.back_color)
    img = img.resize((config.size, config.size))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
