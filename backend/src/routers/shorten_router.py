"""Endpoint 1: crear un enlace corto."""

from fastapi import APIRouter, HTTPException, status

from crud.link_crud import DatabaseError
from schemas.link_schema import ErrorResponse, ShortenRequest, ShortenResponse
from security.url_validator import InvalidUrlError
from services import link_service

router = APIRouter(tags=["Enlaces"])


@router.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un enlace corto",
    responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def shorten(payload: ShortenRequest) -> ShortenResponse:
    try:
        link = link_service.shorten_url(payload.original_url)
    except InvalidUrlError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except DatabaseError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo guardar el enlace en la base de datos."
        ) from error

    return ShortenResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=link_service.build_short_url(link.short_code),
    )
