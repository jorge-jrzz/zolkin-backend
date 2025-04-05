"""
Chat routes for the Zolkin application.
"""
import logging

from fastapi import APIRouter, HTTPException, Request, Query
from langchain_core.messages import HumanMessage

from services.agent import AgentManager


logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter(prefix="/chat", tags=["chat"])

# Instanciar el gestor de agentes
agent_manager = AgentManager()


@router.get("/")
async def chat(
    request: Request,
    prompt: str = Query(..., description="Mensaje del usuario"),
    thread_id: str = Query(..., description="ID del hilo de conversación"),
    use_rag: bool = Query(False, description="Usar RAG para la respuesta"),
):
    """
    Procesa un mensaje del usuario y devuelve la respuesta del agente.
    
    Args:
        request: Objeto de solicitud de FastAPI
        prompt: Mensaje del usuario
        thread_id: ID del hilo de conversación
        use_rag: Indica si se debe usar RAG para la respuesta
        redis: Conexión a Redis
        
    Returns:
        Dict: Respuesta del agente
    """
    # Verificar autenticación
    user_email = request.session.get("user_email")
    if not user_email:
        logger.warning("Usuario no autenticado en endpoint de chat")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    logger.info(f"Solicitud de chat recibida para usuario: {user_email}")

    zolkin_agent = agent_manager.get_zolkin(user_email)
    logger.info(f"ZolkinAgent obtenido para usuario: {user_email}")
    print(type(zolkin_agent))
    if not zolkin_agent:
        logger.error(f"Agente no encontrado en caché para usuario: {user_email}")
        raise HTTPException(status_code=500, detail="Agente no encontrado en caché")
    
    # Obtener el agente LangGraph
    agent = agent_manager.get_agent(user_email)
    logger.info(f"Agente LangGraph obtenido para usuario: {user_email}")
    print(type(agent))
    if not agent:
        logger.error(f"Agente LangGraph no inicializado para usuario: {user_email}")
        raise HTTPException(status_code=500, detail="Agente no inicializado")
    
    # Configurar el prompt para usar RAG si es necesario
    if use_rag:
        enhanced_prompt = f"Utiliza la herramienta de RAG para responder el siguiente prompt: \n{prompt}"
        logger.info("Usando herramienta RAG para solicitud de chat")
    else:
        enhanced_prompt = prompt
    
    logger.info(f"Prompt recibido: {prompt}, Thread ID: {thread_id}")
    
    # Configurar el hilo de conversación
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        response = agent.invoke(
            {"messages": [HumanMessage(content=enhanced_prompt)]}, 
            config=config
        )
        # Verificar la respuesta
        if "messages" not in response or not response["messages"]:
            logger.error("No se encontraron mensajes en la respuesta del agente")
            raise HTTPException(status_code=500, detail="Respuesta del agente inválida")
        
        # Extraer el contenido del último mensaje
        final_response = response["messages"][-1].content
        
        logger.info("Solicitud de chat procesada exitosamente")
        return {
            "response": final_response,
            "thread_id": thread_id,
            "user_email": user_email
        }
    
    except Exception as e:
        logger.error(f"Error al invocar al agente para usuario {user_email}: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud") from e
