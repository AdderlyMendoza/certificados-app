"""Lectura y validación de datasets (Excel/CSV/ODS) con detección de columnas."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.exceptions import ValidationError
from app.schemas.generation import DatasetPreview

_SUPPORTED = {".xlsx", ".xls", ".csv", ".ods"}


def _read_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED:
        raise ValidationError(
            f"Formato no soportado: {suffix}. Use {', '.join(sorted(_SUPPORTED))}"
        )
    try:
        if suffix == ".csv":
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
        elif suffix == ".ods":
            df = pd.read_excel(path, dtype=str, engine="odf", keep_default_na=False)
        else:
            df = pd.read_excel(path, dtype=str, keep_default_na=False)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"No se pudo leer el archivo: {exc}") from exc

    # Normaliza nombres de columnas (sin espacios sobrantes)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def detect_columns(path: Path) -> list[str]:
    """Devuelve los nombres de columna = variables disponibles."""
    return list(_read_dataframe(path).columns)


def read_rows(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Devuelve (columnas, filas como dicts) de todo el dataset."""
    df = _read_dataframe(path)
    columns = list(df.columns)
    rows = df.to_dict(orient="records")
    return columns, rows


def preview(path: Path, limit: int = 10) -> DatasetPreview:
    """Genera una vista previa con validaciones básicas."""
    df = _read_dataframe(path)
    columns = list(df.columns)
    errors: list[str] = []

    if not columns:
        errors.append("El archivo no contiene columnas")
    duplicated = {c for c in columns if columns.count(c) > 1}
    if duplicated:
        errors.append(f"Columnas duplicadas: {', '.join(duplicated)}")
    empty_named = [i for i, c in enumerate(columns) if not c]
    if empty_named:
        errors.append("Existen columnas sin nombre")

    return DatasetPreview(
        columns=columns,
        rows=df.head(limit).to_dict(orient="records"),
        total_rows=len(df),
        errors=errors,
    )
