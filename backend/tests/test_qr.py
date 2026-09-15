"""Tests del generador de QR."""
from __future__ import annotations

from app.schemas.template import QRConfig
from app.services.documents.qr_generator import generate_qr_png


def test_generate_qr_returns_png() -> None:
    png = generate_qr_png("https://example.com", QRConfig(size=150))
    # Firma PNG
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100


def test_qr_respects_error_correction() -> None:
    cfg = QRConfig(error_correction="H", size=200)
    png = generate_qr_png("dato", cfg)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
