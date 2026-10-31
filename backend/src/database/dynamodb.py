"""Conexión con Amazon DynamoDB mediante Boto3.

No se pasan access keys: Boto3 resuelve las credenciales con su cadena por
defecto. En EC2 las obtiene del rol IAM (Instance Metadata Service).
"""

from functools import lru_cache

import boto3

from config import get_settings


@lru_cache
def get_dynamodb_resource():
    settings = get_settings()
    if settings.dynamodb_endpoint_url:
        # DynamoDB Local acepta cualquier credencial: se usan valores ficticios
        # para no depender de las credenciales reales de AWS en desarrollo.
        return boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            endpoint_url=settings.dynamodb_endpoint_url,
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
    return boto3.resource("dynamodb", region_name=settings.aws_region)


def get_links_table():
    """Devuelve la tabla de enlaces configurada en DYNAMODB_TABLE."""
    return get_dynamodb_resource().Table(get_settings().dynamodb_table)
