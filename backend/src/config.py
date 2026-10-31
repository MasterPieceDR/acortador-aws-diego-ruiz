"""Configuración central de la aplicación.

Todos los valores se leen desde variables de entorno (o desde un archivo .env
en desarrollo). Nunca se guardan credenciales de AWS aquí: en EC2 Boto3 usa las
credenciales temporales del rol IAM asociado a la instancia.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    """Convierte 'a, b ,c' en ['a', 'b', 'c'] descartando vacíos."""
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Acortador de enlaces - Diego Ruiz"))
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    aws_region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    dynamodb_table: str = field(default_factory=lambda: os.getenv("DYNAMODB_TABLE", "shortener-links-diego"))
    # Solo para pruebas locales (DynamoDB Local / moto). En AWS se deja vacío.
    dynamodb_endpoint_url: str | None = field(default_factory=lambda: os.getenv("DYNAMODB_ENDPOINT_URL") or None)
    # URL pública del backend, usada para construir el short_url.
    public_base_url: str = field(
        default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    )
    # Orígenes permitidos por CORS (URL del sitio en S3 / CloudFront).
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"))
    )
    max_url_length: int = field(default_factory=lambda: int(os.getenv("MAX_URL_LENGTH", "2048")))


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia de configuración (patrón singleton)."""
    return Settings()
