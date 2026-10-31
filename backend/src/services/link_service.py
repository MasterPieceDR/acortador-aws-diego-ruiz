"""Lógica de negocio del acortador.

Aquí se genera el UUID (siempre en el backend), se valida la URL y se
construye el enlace corto. Los routers solo llaman a estas funciones.
"""

import uuid
from datetime import datetime, timezone

from config import get_settings
from crud import link_crud
from models.link_model import ShortLink
from security.url_validator import is_valid_short_code, validate_original_url

MAX_CREATE_ATTEMPTS = 3


class LinkNotFoundError(Exception):
    """No existe un enlace con ese short_code."""


def build_short_url(short_code: str) -> str:
    return f"{get_settings().public_base_url}/{short_code}"


def shorten_url(raw_url: str) -> ShortLink:
    settings = get_settings()
    original_url = validate_original_url(raw_url, settings.max_url_length, settings.public_base_url)

    # Una colisión de UUID v4 es casi imposible, pero se reintenta por seguridad.
    for _ in range(MAX_CREATE_ATTEMPTS):
        link = ShortLink(
            short_code=str(uuid.uuid4()),
            original_url=original_url,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        try:
            return link_crud.create_link(link)
        except link_crud.DuplicateCodeError:
            continue
    raise link_crud.DatabaseError("No se pudo generar un código único.")


def resolve_link(short_code: str) -> ShortLink:
    # Un código con formato inválido no puede existir: no se consulta la BD.
    if not is_valid_short_code(short_code):
        raise LinkNotFoundError(short_code)
    link = link_crud.get_link(short_code.lower())
    if link is None:
        raise LinkNotFoundError(short_code)
    return link
