"""Punto de entrada de la API.

Une todos los módulos mediante routers. Ejecutar desde la carpeta backend:
    Desarrollo:  fastapi dev src/main.py
    Producción:  fastapi run src/main.py --port 8000
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config import get_settings
from routers import health_router, redirect_router, shorten_router, urls_router
from security.http_security import setup_security

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("shortener")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para acortar enlaces con FastAPI, Amazon DynamoDB y Amazon EC2.",
    version="1.0.0",
)

setup_security(app)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Errores de cuerpo JSON (campo faltante, tipo incorrecto, JSON mal formado)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Solicitud inválida: envía un JSON con el campo 'original_url' de tipo texto."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor."},
    )


# Orden importante: el router de redirección (/{short_code}) va al final.
app.include_router(health_router.router)
app.include_router(shorten_router.router)
app.include_router(urls_router.router)
app.include_router(redirect_router.router)
