"""Endpoint para previsualizar códigos QR configurables."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.dependencies import CurrentUser
from app.schemas.template import QRConfig
from app.services.documents.qr_generator import generate_qr_png

router = APIRouter(prefix="/qr", tags=["qr"])


@router.post("/preview")
async def preview_qr(_: CurrentUser, content: str, config: QRConfig) -> Response:
    """Genera un PNG del QR con el contenido y configuración dados."""
    png = generate_qr_png(content, config)
    return Response(content=png, media_type="image/png")
