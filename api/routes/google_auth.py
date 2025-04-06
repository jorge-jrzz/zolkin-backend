"""
Google OAuth2 authentication routes for the Zolkin application.
"""
import os
import logging

from starlette.config import Config
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, HTTPException, Request
from authlib.integrations.starlette_client import OAuth, OAuthError

from services import GoogleAuthManager, UserManager
from ..utils import ensure_ssl_for_ngrok
from ..init_agent import init_agent


logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter(prefix="/google", tags=["google"])

config = Config()
oauth = OAuth(config)

# Definir los scopes necesarios para Google
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://mail.google.com/",
    "openid",
    "email",
    "profile"
]

# URL de configuración de OpenID de Google
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Registrar el cliente de Google
oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    client_kwargs={"scope": " ".join(SCOPES)}
)

# Instanciar el gestor de autenticación de Google
auth_manager = GoogleAuthManager()
# Instanciar el gestor de usuarios
user_manager = UserManager()


@router.get("/")
async def google_login(request: Request):
    """
    Inicia el flujo de autenticación OAuth2 con Google.
    
    Args:
        request: Objeto de solicitud de FastAPI
        
    Returns:
        RedirectResponse: Redirección a la página de autenticación de Google
    """
    try:
        logger.info("Iniciando flujo de autenticación OAuth2 con Google")
        
        # Generar la URL de redirección
        redirect_uri = request.url_for("google_auth")
        
        # Forzar HTTPS si estamos usando ngrok
        redirect_uri = ensure_ssl_for_ngrok(redirect_uri)
        
        # Iniciar el flujo de OAuth2
        return await oauth.google.authorize_redirect(
            request,
            redirect_uri,
            access_type="offline",
            prompt="consent"
        )
    except Exception as e:
        logger.error(f"Error al iniciar el flujo de autenticación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al iniciar la autenticación con Google"
        ) from e


@router.get("/auth/")
async def google_auth(request: Request):
    """
    Callback para la autenticación de Google.
    
    Args:
        request: Objeto de solicitud de FastAPI
        
    Returns:
        RedirectResponse: Redirección al frontend después de la autenticación
    """
    try:
        logger.info("Recibido callback de autenticación de Google")
        
        # Obtener el token de acceso
        token = await oauth.google.authorize_access_token(request)
        if not token:
            logger.error("No se pudo obtener el token de acceso")
            raise HTTPException(status_code=400, detail="Autorización fallida")
        
        # Obtener información del usuario
        user_info = token.get('userinfo', {})
        if not user_info:
            logger.error("No se pudo obtener la información del usuario")
            raise HTTPException(status_code=400, detail="Error al obtener información del usuario")
        
        # Extraer email del usuario
        user_email = user_info.get("email")
        if not user_email:
            logger.error("No se pudo obtener el email del usuario")
            raise HTTPException(status_code=400, detail="Email de usuario no disponible")
        
        logger.info(f"Usuario autenticado: {user_email}")
        
        # Crear credenciales de Google
        try:
            # Crear credenciales usando el gestor de autenticación
            credentials = auth_manager.create_credentials(token, SCOPES)
            auth_manager.save_credentials(credentials, user_email)
            logger.debug(f"Credenciales de Google guardadas para {user_email}")
        except Exception as e:
            logger.error(f"Error al crear credenciales de Google: {e}")
            raise HTTPException(status_code=500, detail="Error de credenciales") from e
        
        # Preparar datos del usuario
        user_info_data = {
            "name": user_info.get("name", ""),
            "email": user_email,
            "picture": user_info.get("picture", ""),
            "given_name": user_info.get("given_name", ""),
            "family_name": user_info.get("family_name", ""),
        }
        
        # Guardar información del usuario
        user_manager.set_user(user_email, user_info_data)
        
        # Establecer la sesión de manera explícita
        request.session.clear()
        request.session["user_email"] = user_email
        request.session["authenticated"] = True
        
        # Inicializamos el agente Zolkin
        init_agent(user_email, credentials)
        logger.info(f"Agente y datos de usuario configurados para: {user_email}")
        
        # Redireccionar al frontend
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        logger.info(f"Redirigiendo al usuario a {frontend_url}/chat")
        
        return RedirectResponse(url=f"{frontend_url}/chat")
    
    except OAuthError as e:
        logger.error(f"Error de OAuth: {e}")
        raise HTTPException(status_code=400, detail=f"Error de OAuth: {str(e)}") from e
    
    except Exception as e:
        logger.error(f"Error inesperado durante la autenticación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor") from e
