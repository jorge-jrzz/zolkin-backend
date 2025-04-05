"""
API routes for the Zolkin application.
"""
from fastapi import APIRouter

from .google_auth import router as google_router
from .chat import router as chat_router
from .files import router as files_router
from .users import router as users_router


__all__ = ["api_router"]


api_router = APIRouter()

# Incluir los routers de las diferentes funcionalidades
api_router.include_router(google_router)
api_router.include_router(chat_router)
api_router.include_router(files_router)
api_router.include_router(users_router)
