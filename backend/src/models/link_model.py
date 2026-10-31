"""Modelo de dominio: un enlace corto tal como se guarda en DynamoDB."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ShortLink:
    short_code: str  # UUID v4, clave de partición de la tabla
    original_url: str
    created_at: str  # ISO 8601 en UTC

    def to_item(self) -> dict[str, Any]:
        """Convierte el modelo en un elemento de DynamoDB."""
        return {
            "short_code": self.short_code,
            "original_url": self.original_url,
            "created_at": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> "ShortLink":
        """Reconstruye el modelo a partir de un elemento de DynamoDB."""
        return cls(
            short_code=str(item["short_code"]),
            original_url=str(item["original_url"]),
            created_at=str(item["created_at"]),
        )
