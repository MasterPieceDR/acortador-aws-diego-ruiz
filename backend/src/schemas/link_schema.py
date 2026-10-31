"""Esquemas Pydantic: contratos de entrada y salida de la API."""

from pydantic import BaseModel, ConfigDict, Field


class ShortenRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"original_url": "https://www.example.com/articulos/arquitectura-cloud"}},
    )

    original_url: str = Field(..., description="URL original que se desea acortar.")


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


class LinkInfoResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: str


class ErrorResponse(BaseModel):
    detail: str
