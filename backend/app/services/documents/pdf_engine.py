"""Motor PDF: vista previa, overlay de campos por coordenadas y generación.

El PDF original actúa como fondo inmutable. Sobre él se "pintan" los campos
definidos en el layout (texto, variables, QR, imágenes) usando PyMuPDF (fitz).

Sistema de coordenadas: el editor visual usa origen ARRIBA-IZQUIERDA en
píxeles a 1x (72 DPI = puntos PDF), que coincide con el sistema de PyMuPDF.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from app.models.enums import FieldType
from app.schemas.template import LayoutField, QRConfig, TemplateLayout
from app.services.documents.qr_generator import generate_qr_png

# Mapa de fuentes lógicas -> fuentes base de PyMuPDF
_FONT_MAP = {
    ("helvetica", False, False): "helv",
    ("helvetica", True, False): "hebo",
    ("helvetica", False, True): "heit",
    ("helvetica", True, True): "hebi",
    ("times", False, False): "tiro",
    ("times", True, False): "tibo",
    ("times", False, True): "tiit",
    ("times", True, True): "tibi",
    ("courier", False, False): "cour",
    ("courier", True, False): "cobo",
}


def _resolve_font(field: LayoutField) -> str:
    key = (field.font.lower().split()[0], field.bold, field.italic)
    return _FONT_MAP.get(key, "helv")


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    color = color.lstrip("#")
    if len(color) != 6:
        return (0.0, 0.0, 0.0)
    return tuple(int(color[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def render_preview(pdf_path: Path, page: int = 0, zoom: float = 2.0) -> bytes:
    """Renderiza una página del PDF como PNG (para el editor visual)."""
    with fitz.open(str(pdf_path)) as doc:
        page_obj = doc[page]
        matrix = fitz.Matrix(zoom, zoom)
        pix = page_obj.get_pixmap(matrix=matrix)
        return pix.tobytes("png")


def get_page_size(pdf_path: Path, page: int = 0) -> tuple[float, float]:
    """Devuelve (ancho, alto) en puntos PDF de una página."""
    with fitz.open(str(pdf_path)) as doc:
        rect = doc[page].rect
        return rect.width, rect.height


def _draw_text(page: "fitz.Page", field: LayoutField, text: str) -> None:
    import logging
    log = logging.getLogger("pdf_engine")
    log.warning("FIELD: name=%s align=%s x=%.1f y=%.1f font_size=%.1f auto_fit=%s width=%s text=%s", field.name, field.align, field.x, field.y, field.font_size, field.auto_fit, field.width, text[:40])

    rgb = _hex_to_rgb(field.color)
    fontname = _resolve_font(field)
    font = fitz.Font(fontname)

    font_size = field.font_size
    if field.auto_fit and field.width and field.width > 0:
        text_width = font.text_length(text, fontsize=font_size)
        if text_width > field.width:
            font_size = max(4, font_size * field.width / text_width)

    text_width = font.text_length(text, fontsize=font_size)
    page_width = page.rect.width

    if field.align == "center":
        x = field.x - text_width / 2
    elif field.align == "right":
        x = field.x - text_width
    else:
        x = field.x

    x = max(0, min(x, page_width - text_width))
    y = field.y + font_size

    log.warning("DRAW: x=%.1f y=%.1f font_size=%.1f text_width=%.1f page_width=%.1f", x, y, font_size, text_width, page_width)

    point = fitz.Point(x, y)
    page.insert_text(
        point, text, fontname=fontname, fontsize=font_size, color=rgb
    )


def _draw_image(page: "fitz.Page", field: LayoutField, image_bytes: bytes) -> None:
    width = field.width or 100
    height = field.height or 100
    rect = fitz.Rect(field.x, field.y, field.x + width, field.y + height)
    page.insert_image(rect, stream=image_bytes, keep_proportion=True)


def generate(
    pdf_path: Path,
    layout: TemplateLayout,
    context: dict[str, Any],
    output_path: Path,
    *,
    qr_config: QRConfig | None = None,
) -> Path:
    """Genera un PDF final aplicando los campos del layout sobre el fondo."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(str(pdf_path)) as doc:
        for field in layout.fields:
            if field.page >= len(doc):
                continue
            page = doc[field.page]

            if field.type in (FieldType.TEXT, FieldType.VARIABLE, FieldType.DATE, FieldType.NUMBER):
                text = _resolve_text(field, context)
                if text:
                    _draw_text(page, field, text)

            elif field.type == FieldType.QR:
                cfg = qr_config or QRConfig()
                content = _render_template_str(cfg.content_template, context)
                qr_png = generate_qr_png(content, cfg)
                _draw_image(page, field, qr_png)

            elif field.type in (FieldType.IMAGE, FieldType.SIGNATURE):
                img = context.get(field.name)
                if isinstance(img, (bytes, bytearray)):
                    _draw_image(page, field, bytes(img))
                elif isinstance(img, str) and Path(img).exists():
                    _draw_image(page, field, Path(img).read_bytes())

        doc.save(str(output_path), garbage=4, deflate=True)
    return output_path


def _resolve_text(field: LayoutField, context: dict[str, Any]) -> str:
    """Resuelve el texto de un campo: valor fijo, variable o plantilla."""
    if field.value:
        return _render_template_str(field.value, context)
    raw = context.get(field.name, "")
    return "" if raw is None else str(raw)


def _render_template_str(template: str, context: dict[str, Any]) -> str:
    """Sustituye {{ var }} simples por valores del contexto."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace(f"{{{{ {key} }}}}", str(value))
    return result
