"""Endpoints de estado del servicio."""

from fastapi import APIRouter

from config import get_settings

router = APIRouter(tags=["Estado"])


@router.get("/", summary="Información de la API")
def root() -> dict[str, str]:
    return {"app": get_settings().app_name, "docs": "/docs", "status": "ok"}


@router.get("/health", summary="Verificación de salud")
def health() -> dict[str, str]:
    return {"status": "ok"}
