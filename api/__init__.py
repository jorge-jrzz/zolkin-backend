"""
API package for the Zolkin application.
"""
import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from .routes import api_router


def create_app(cors_origins: List[str]) -> FastAPI:
    """
    Creates and configures the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Crear la aplicación FastAPI
    app = FastAPI(
        title="Zolkin API",
        description="API para el asistente Zolkin con Herramientas de Google y RAG",
        version="0.2.0",
    )
    
    # Configurar middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add ProxyHeadersMiddleware to handle forwarded headers
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    
    # Configurar middleware de sesiones
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "supersecretkey"),
        max_age=3600,  # 1 hora
        https_only=True,  # Force HTTPS for cookies
        same_site="none",  # Allow cross-site cookies for frontend integration
    )
    
    # Incluir las rutas de la API
    app.include_router(api_router)
    
    return app
