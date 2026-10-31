"""Validaciones de seguridad para las URL y los códigos cortos."""

import ipaddress
import re
import uuid
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}
# Dominio: etiquetas alfanuméricas (con guiones internos) y un TLD alfabético.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:(?!-)[a-z0-9-]{1,63}(?<!-)\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$",
    re.IGNORECASE,
)
_FORBIDDEN_CHARS_RE = re.compile(r"[\s<>\"{}|\\^`\x00-\x1f\x7f]")


class InvalidUrlError(ValueError):
    """La URL enviada no es válida para ser acortada."""


def _is_valid_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return bool(_DOMAIN_RE.match(ascii_host))


def validate_original_url(raw_url: str, max_length: int, own_base_url: str) -> str:
    """Valida la URL y la devuelve limpia, o lanza InvalidUrlError."""
    url = (raw_url or "").strip()

    if not url:
        raise InvalidUrlError("La URL es obligatoria.")
    if len(url) > max_length:
        raise InvalidUrlError(f"La URL supera el máximo de {max_length} caracteres.")
    if _FORBIDDEN_CHARS_RE.search(url):
        raise InvalidUrlError("La URL contiene espacios o caracteres no permitidos.")

    try:
        parts = urlsplit(url)
        port = parts.port  # lanza ValueError si el puerto es inválido
    except ValueError as error:
        raise InvalidUrlError("La URL tiene un formato inválido.") from error

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise InvalidUrlError("La URL debe comenzar con http:// o https://.")
    if not parts.hostname or not _is_valid_host(parts.hostname):
        raise InvalidUrlError("La URL no tiene un dominio válido (ejemplo: https://www.ejemplo.com).")
    if parts.username or parts.password:
        raise InvalidUrlError("La URL no debe incluir usuario ni contraseña.")
    if port == 0:
        raise InvalidUrlError("La URL tiene un puerto inválido.")

    # Evita bucles: no se permite acortar un enlace del propio acortador.
    own = urlsplit(own_base_url)
    if parts.hostname == own.hostname and (port or _default_port(parts.scheme)) == (
        own.port or _default_port(own.scheme)
    ):
        raise InvalidUrlError("No se puede acortar un enlace que ya pertenece a este acortador.")

    return url


def _default_port(scheme: str) -> int:
    return 443 if scheme.lower() == "https" else 80


def is_valid_short_code(short_code: str) -> bool:
    """Comprueba que el código sea un UUID canónico (36 caracteres)."""
    try:
        return str(uuid.UUID(short_code)) == short_code.lower()
    except (ValueError, AttributeError, TypeError):
        return False
