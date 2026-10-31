"""CORS y cabeceras de seguridad HTTP."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def setup_security(app: FastAPI) -> None:
    settings = get_settings()

    # Solo el origen de la interfaz web (S3 / CloudFront) puede llamar a la API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
        max_age=600,
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response
