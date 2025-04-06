"""
API routes for the Zolkin application.
"""
from fastapi import APIRouter

from .chat import router as chat_router
from .files import router as files_router
from .users import router as users_router
from .google_auth import router as google_router


__all__ = ["api_router"]


api_router = APIRouter()

api_router.include_router(chat_router)
api_router.include_router(files_router)
api_router.include_router(users_router)
api_router.include_router(google_router)
