"""Endpoint 3: consultar la información de un enlace."""

from fastapi import APIRouter, HTTPException, status

from crud.link_crud import DatabaseError
from schemas.link_schema import ErrorResponse, LinkInfoResponse
from services import link_service

router = APIRouter(prefix="/urls", tags=["Enlaces"])


@router.get(
    "/{short_code}",
    response_model=LinkInfoResponse,
    summary="Consultar un enlace",
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_link_info(short_code: str) -> LinkInfoResponse:
    try:
        link = link_service.resolve_link(short_code)
    except link_service.LinkNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El enlace corto no existe.") from error
    except DatabaseError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo consultar la base de datos.") from error

    return LinkInfoResponse(short_code=link.short_code, original_url=link.original_url, created_at=link.created_at)
