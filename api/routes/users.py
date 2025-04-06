"""
User information routes for the Zolkin application.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request

from services import UserManager


logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter(prefix="/user_info", tags=["user_info"])

# Instanciar el gestor de usuarios
user_manager = UserManager()


@router.get("/")
async def user_info(request: Request) -> Dict[str, Any]:
    """
    Endpoint para obtener la información del usuario.
    
    Args:
        request: Objeto de solicitud de FastAPI
        
    Returns:
        Dict[str, Any]: Información del usuario
        
    Raises:
        HTTPException: Si el usuario no está autenticado o no se encuentra
    """
    # Verificar autenticación del usuario
    user_email = request.session.get("user_email")
    if not user_email:
        logger.warning("Usuario no autenticado al acceder al endpoint user_info")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    logger.info(f"Obteniendo información de usuario para: {user_email}")
    
    # Intentar obtener el usuario del gestor de usuarios
    user = user_manager.get_user(user_email)
    
    if user is None:
        logger.error(f"Usuario no encontrado para el email: {user_email}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logger.info(f"Información de usuario recuperada correctamente para {user_email}")
    return user
