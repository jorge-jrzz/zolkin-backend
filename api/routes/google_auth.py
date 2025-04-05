"""
Google OAuth2 authentication routes for the Zolkin application.
"""
import os
import logging

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, HTTPException, Request
from authlib.integrations.starlette_client import OAuth, OAuthError

from services import get_redis_conn
from services.auth import GoogleAuthManager, UserManager, set_user
from services.agent import ZolkinAgent, MilvusStorage, RedisSaver, AgentManager


# Configuración del logger
logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter(prefix="/google", tags=["google"])

oauth = OAuth()

# Definir los scopes necesarios para Google
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
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
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={"scope": " ".join(SCOPES)}
)

# Instanciar el gestor de autenticación de Google
auth_manager = GoogleAuthManager()

# Instanciar el gestor de usuarios
user_manager = UserManager()

# Instanciar el gestor de agentes
agent_manager = AgentManager()


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
        )


@router.get("/auth/")
async def google_auth(request: Request):
    """
    Callback para la autenticación de Google.
    
    Args:
        request: Objeto de solicitud de FastAPI
        redis: Conexión a Redis
        
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
        # Verificar si id_token está presente en el token
        try:
            if 'id_token' not in token:
                # Si no está presente, obtener información del usuario usando userinfo endpoint
                logger.debug(f"Token no contiene id_token, usando endpoint userinfo. Token keys: {token.keys()}")
                resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
                user_info = resp.json()
            else:
                # Si está presente, usar el método original
                user_info = await oauth.google.parse_id_token(request, token)
                
            logger.debug(f"Información de usuario obtenida: {user_info.keys() if user_info else None}")
        except Exception as e:
            logger.error(f"Error al obtener información del usuario: {e}")
            # Intentar obtener información básica del token
            user_info = {}
            if 'userinfo' in token:
                user_info = token.get('userinfo', {})
            elif 'access_token' in token:
                # Último intento: usar el access_token directamente
                try:
                    import requests
                    headers = {'Authorization': f'Bearer {token["access_token"]}'}
                    response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
                    if response.status_code == 200:
                        user_info = response.json()
                except Exception as req_error:
                    logger.error(f"Error al obtener userinfo con requests: {req_error}")
            
            if not user_info:
                raise HTTPException(status_code=400, detail="Error al obtener información del usuario")
        
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
            
            # Guardar credenciales
            auth_manager.save_credentials(credentials, user_email)
            logger.debug(f"Credenciales de Google guardadas para {user_email}")
        except Exception as e:
            logger.error(f"Error al crear credenciales de Google: {e}")
            raise HTTPException(status_code=500, detail="Error de credenciales")
        
        # Preparar datos del usuario
        user_info_data = {
            "name": user_info.get("name", ""),
            "email": user_email,
            "picture": user_info.get("picture", ""),
            "given_name": user_info.get("given_name", ""),
            "family_name": user_info.get("family_name", ""),
            "locale": user_info.get("locale", "es"),
        }
        
        # Guardar información del usuario
        user_manager.set_user(user_email, user_info_data)
        
        # Para compatibilidad con código anterior
        set_user(user_email, user_info_data)
        
        # Inicializar Milvus para RAG
        try:
            collection_name = os.getenv("MILVUS_COLLECTION", "zolkin_collection")
            milvus_conn = MilvusStorage(collection_name=collection_name)
            milvus_storage = milvus_conn.use_collection()
            
            if not milvus_storage:
                logger.warning(f"No se pudo inicializar el almacenamiento Milvus para {user_email}")
        except Exception as e:
            logger.error(f"Error al inicializar Milvus: {e}")
            raise HTTPException(status_code=500, detail="Error al inicializar el sistema de RAG")
        
        # Inicializar el agente Zolkin
        try:
            # In the google_auth.py file, modify the google_auth function:
            
            # After creating the zolkin_agent and initializing tools
            zolkin_agent = ZolkinAgent(
                google_creds=credentials,
                milvus_conn=milvus_conn,
                milvus_storage=milvus_storage,
                partition_key_field=user_email,
            )
            
            # Inicializar herramientas
            zolkin_agent = zolkin_agent.init_tools()
            
            # Store the ZolkinAgent instance in both the global dictionary and the agent manager
            agent_manager.set_zolkin(user_email, zolkin_agent)
            logger.info(f"Agente Zolkin inicializado para {user_email}")
            
            # Inicializar memoria del agente
            redis_conn = get_redis_conn()
            memory = RedisSaver(redis_conn)
            
            # Crear el agente con memoria
            agent = zolkin_agent.create_agent(memory)
            
            # Store the LangGraph agent in the agent manager
            agent_manager.set_agent(user_email, agent)
            
            # Store only the user email in the session, not the agent
            request.session["user_email"] = user_email
            
            logger.info(f"Agente y datos de usuario configurados para: {user_email}")
        except Exception as e:
            logger.error(f"Error al inicializar el agente Zolkin: {e}")
            raise HTTPException(status_code=500, detail="Error al inicializar el asistente")
        
        # Redireccionar al frontend
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        logger.info(f"Redirigiendo al usuario a {frontend_url}/chat")
        
        return RedirectResponse(url=f"{frontend_url}/chat")
    
    except OAuthError as e:
        logger.error(f"Error de OAuth: {e}")
        raise HTTPException(status_code=400, detail=f"Error de OAuth: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error inesperado durante la autenticación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/user")
async def get_current_user(request: Request):
    """
    Obtiene la información del usuario actual.
    
    Args:
        request: Objeto de solicitud de FastAPI
        
    Returns:
        Dict: Información del usuario o mensaje de error
    """
    user_email = request.session.get("user_email")
    
    if not user_email:
        return {"authenticated": False, "message": "No hay usuario autenticado"}
    
    user_data = user_manager.get_user(user_email)
    
    if not user_data:
        return {"authenticated": False, "message": "Usuario no encontrado"}
    
    return {
        "authenticated": True,
        "user": user_data
    }
