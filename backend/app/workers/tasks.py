"""Tareas Celery: procesamiento de la generación masiva de documentos."""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from app.models.enums import GenerationStatus, TemplateType
from app.models.generation import Generation, GenerationItem
from app.models.template import Template
from app.schemas.template import QRConfig, TemplateLayout
from app.services.documents import dataset_reader, pdf_engine, word_engine
from app.utils.files import generated_path
from app.workers.celery_app import celery_app
from app.workers.db_sync import SyncSessionLocal


def _build_context(row: dict[str, Any], mapping: dict[str, str] | None) -> dict[str, Any]:
    """Construye el contexto de variables aplicando el mapeo de columnas."""
    if not mapping:
        return dict(row)
    context = dict(row)
    for column, variable in mapping.items():
        if column in row:
            context[variable] = row[column]
    return context


def _generate_one(
    template: Template, context: dict[str, Any], out_dir: Path, index: int,
    used_names: set[str] | None = None,
) -> Path:
    """Genera un único documento PDF a partir de la plantilla y el contexto."""
    base_name = (
        context.get("nombre_archivo")
        or context.get("nombre")
        or context.get("Nombre")
        or f"documento_{index + 1}"
    )
    safe_name = "".join(c for c in str(base_name) if c.isalnum() or c in " -_").strip()
    if not safe_name:
        safe_name = f"documento_{index + 1}"

    if used_names is not None:
        original = safe_name
        counter = 2
        while safe_name in used_names:
            safe_name = f"{original}_{counter}"
            counter += 1
        used_names.add(safe_name)

    output_pdf = out_dir / f"{safe_name}.pdf"

    if template.type == TemplateType.WORD:
        tmp_docx = out_dir / f"_tmp_{index}.docx"
        word_engine.render_docx(Path(template.file_path), context, tmp_docx)
        pdf = word_engine.convert_to_pdf(tmp_docx, out_dir)
        pdf.replace(output_pdf)
        tmp_docx.unlink(missing_ok=True)
    else:
        layout = TemplateLayout(**(template.layout or {"page_width": 0, "page_height": 0}))
        qr_cfg = QRConfig(**template.qr_config) if template.qr_config else None
        pdf_engine.generate(
            Path(template.file_path), layout, context, output_pdf, qr_config=qr_cfg
        )
    return output_pdf


@celery_app.task(bind=True, name="generation.run")
def run_generation(self, generation_id: int) -> dict[str, Any]:  # noqa: ANN001
    """Procesa una generación completa: documento por fila + ZIP final."""
    session = SyncSessionLocal()
    try:
        gen = session.get(Generation, generation_id)
        if gen is None:
            return {"error": "generación no encontrada"}

        template = session.get(Template, gen.template_id)
        if template is None:
            gen.status = GenerationStatus.FAILED
            gen.error_message = "Plantilla no encontrada"
            session.commit()
            return {"error": gen.error_message}

        gen.status = GenerationStatus.PROCESSING
        session.commit()

        _, rows = dataset_reader.read_rows(Path(gen.dataset_path))
        out_dir = generated_path(f"gen_{gen.id}", "files").parent
        files_dir = out_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        produced: list[Path] = []
        used_names: set[str] = set()
        for index, row in enumerate(rows):
            # Cancelación cooperativa: revisa el estado cada fila
            session.refresh(gen)
            if gen.status == GenerationStatus.CANCELLED:
                return {"status": "cancelled", "processed": gen.processed_rows}

            context = _build_context(row, gen.column_mapping)
            item = GenerationItem(
                generation_id=gen.id, row_index=index, row_data=row
            )
            try:
                pdf = _generate_one(template, context, files_dir, index, used_names)
                produced.append(pdf)
                item.status = GenerationStatus.COMPLETED
                item.output_path = str(pdf)
                gen.processed_rows += 1
            except Exception as exc:  # noqa: BLE001
                item.status = GenerationStatus.FAILED
                item.error_message = str(exc)
                gen.failed_rows += 1
            session.add(item)
            session.commit()

        # Empaqueta en ZIP
        zip_path = out_dir / f"generacion_{gen.id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for pdf in produced:
                zf.write(pdf, arcname=pdf.name)

        gen.zip_path = str(zip_path)
        gen.status = GenerationStatus.COMPLETED
        session.commit()
        return {
            "status": "completed",
            "processed": gen.processed_rows,
            "failed": gen.failed_rows,
            "zip": str(zip_path),
        }
    except Exception as exc:  # noqa: BLE001  # noqa: F841
        session.rollback()
        gen = session.get(Generation, generation_id)
        if gen:
            gen.status = GenerationStatus.FAILED
            gen.error_message = str(exc)
            session.commit()
        raise
    finally:
        session.close()
