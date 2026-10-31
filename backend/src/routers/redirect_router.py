"""Endpoint 2: redirigir al destino original.

Este router se registra al final en main.py porque su ruta /{short_code}
captura cualquier segmento y no debe ocultar /health, /urls o /docs.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from crud.link_crud import DatabaseError
from schemas.link_schema import ErrorResponse
from services import link_service

router = APIRouter(tags=["Redirección"])


@router.get(
    "/{short_code}",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=RedirectResponse,
    summary="Redirigir a la URL original",
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def redirect_to_original(short_code: str) -> RedirectResponse:
    try:
        link = link_service.resolve_link(short_code)
    except link_service.LinkNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El enlace corto no existe.") from error
    except DatabaseError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo consultar la base de datos.") from error

    # Redirección HTTP real: el navegador navega solo hacia la URL original.
    return RedirectResponse(
        url=link.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Cache-Control": "no-store"},
    )
