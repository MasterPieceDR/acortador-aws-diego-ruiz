"""Operaciones de acceso a datos (CRUD) sobre la tabla de DynamoDB.

Solo se usan PutItem y GetItem, que son los únicos permisos que concede el
rol IAM de la instancia EC2 (principio de mínimo privilegio).
"""

import logging

from botocore.exceptions import BotoCoreError, ClientError

from database.dynamodb import get_links_table
from models.link_model import ShortLink

logger = logging.getLogger("dynamodb")


def _log_error(operation: str, error: Exception) -> None:
    """Registra en la terminal la causa real del fallo de DynamoDB."""
    if isinstance(error, ClientError):
        info = error.response.get("Error", {})
        logger.error("%s falló: %s - %s", operation, info.get("Code"), info.get("Message"))
    else:
        logger.error("%s falló: %s", operation, error)


class DatabaseError(Exception):
    """Error al comunicarse con DynamoDB."""


class DuplicateCodeError(Exception):
    """El short_code ya existe en la tabla (colisión de UUID)."""


def create_link(link: ShortLink) -> ShortLink:
    try:
        get_links_table().put_item(
            Item=link.to_item(),
            # Nunca sobrescribir un enlace existente.
            ConditionExpression="attribute_not_exists(short_code)",
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            raise DuplicateCodeError(link.short_code) from error
        _log_error("PutItem", error)
        raise DatabaseError(str(error)) from error
    except BotoCoreError as error:
        _log_error("PutItem", error)
        raise DatabaseError(str(error)) from error
    return link


def get_link(short_code: str) -> ShortLink | None:
    try:
        response = get_links_table().get_item(Key={"short_code": short_code})
    except (ClientError, BotoCoreError) as error:
        _log_error("GetItem", error)
        raise DatabaseError(str(error)) from error

    item = response.get("Item")
    return ShortLink.from_item(item) if item else None
