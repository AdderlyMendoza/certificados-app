"""Tests de utilidades del motor PDF (sin I/O de archivos)."""
from __future__ import annotations

from app.models.enums import FieldType
from app.schemas.template import LayoutField
from app.services.documents.pdf_engine import _hex_to_rgb, _render_template_str, _resolve_font


def test_hex_to_rgb() -> None:
    assert _hex_to_rgb("#000000") == (0.0, 0.0, 0.0)
    assert _hex_to_rgb("#FFFFFF") == (1.0, 1.0, 1.0)
    assert _hex_to_rgb("bad") == (0.0, 0.0, 0.0)


def test_resolve_font_bold_italic() -> None:
    field = LayoutField(name="x", type=FieldType.TEXT, x=0, y=0, bold=True, italic=True)
    assert _resolve_font(field) == "hebi"


def test_render_template_str_replaces_variables() -> None:
    ctx = {"nombre": "Ana", "curso": "Python"}
    assert _render_template_str("{{nombre}} - {{ curso }}", ctx) == "Ana - Python"
