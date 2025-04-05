"""
API package for the Zolkin application.
"""
import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .routes import api_router


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Crear la aplicación FastAPI
    app = FastAPI(
        title="Zolkin API",
        description="API para el asistente Zolkin con integración de Google y RAG",
        version="1.0.0",
    )
    
    # Configurar middleware de sesiones
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "supersecretkey"),
        max_age=3600,  # 1 hora
    )
    
    # Incluir las rutas de la API
    app.include_router(api_router)
    
    return app
