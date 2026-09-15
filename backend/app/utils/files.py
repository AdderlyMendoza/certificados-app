"""Utilidades de almacenamiento de archivos en disco."""
from __future__ import annotations

import uuid
from pathlib import Path

from slugify import slugify

from app.core.config import settings


def ensure_dirs() -> None:
    """Crea los directorios de uploads/generated si no existen."""
    for d in (settings.UPLOAD_DIR, settings.GENERATED_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)


def unique_filename(original: str) -> str:
    """Genera un nombre único conservando la extensión y un slug legible."""
    p = Path(original)
    stem = slugify(p.stem)[:60] or "file"
    return f"{stem}-{uuid.uuid4().hex[:10]}{p.suffix.lower()}"


def save_upload(content: bytes, original_filename: str, subdir: str = "templates") -> Path:
    """Guarda bytes en UPLOAD_DIR/<subdir>/ y devuelve la ruta absoluta."""
    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / unique_filename(original_filename)
    path.write_bytes(content)
    return path


def generated_path(*parts: str) -> Path:
    """Construye una ruta dentro de GENERATED_DIR, creando los directorios."""
    path = Path(settings.GENERATED_DIR, *parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
