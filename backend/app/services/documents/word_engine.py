"""Motor Word: detección de variables, render con docxtpl y conversión a PDF.

La sintaxis de variables es la de Jinja2/docxtpl: ``{{ nombre }}``.
La conversión a PDF usa LibreOffice headless para conservar los estilos.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from app.core.config import settings
from app.core.exceptions import AppException


def detect_variables(docx_path: Path) -> list[str]:
    """Extrae los nombres de variable declarados en la plantilla .docx."""
    tpl = DocxTemplate(str(docx_path))
    # Carga el XML para que docxtpl pueda analizar las variables Jinja2
    variables = tpl.get_undeclared_template_variables()
    return sorted(variables)


def render_docx(template_path: Path, context: dict[str, Any], output_path: Path) -> Path:
    """Renderiza la plantilla con el contexto dado y guarda un .docx."""
    tpl = DocxTemplate(str(template_path))
    # Las claves faltantes se sustituyen por cadena vacía para no romper el render
    safe_context = {k: ("" if v is None else v) for k, v in context.items()}
    tpl.render(safe_context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tpl.save(str(output_path))
    return output_path


def convert_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    """Convierte un .docx a .pdf usando LibreOffice headless."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.SOFFICE_BIN,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(docx_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, check=False
        )
    except FileNotFoundError as exc:
        raise AppException(
            "LibreOffice (soffice) no está instalado o no se encuentra en PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AppException("La conversión a PDF excedió el tiempo límite") from exc

    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        raise AppException(f"Error al convertir a PDF: {result.stderr.strip()}")
    return pdf_path
