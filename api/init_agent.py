"""Function to initialize the agent."""
import os
import logging

from fastapi import HTTPException
from google.oauth2.credentials import Credentials

from services import (
    MilvusStorage,
    ZolkinAgent,
    AgentManager,
    RedisSaver,
    get_redis_conn
)


logger = logging.getLogger(__name__)


def init_agent(user_email: str, credentials: Credentials) -> None:
    """Initialize the agent for the user."""
    # Instanciar el gestor de agentes
    agent_manager = AgentManager()
    # Inicializar Milvus para RAG
    try:
        collection_name = os.getenv("MILVUS_COLLECTION", "zolkin_collection")
        milvus_conn = MilvusStorage(collection_name=collection_name)
        milvus_storage = milvus_conn.use_collection()
        
        if not milvus_storage:
            logger.warning(f"No se pudo inicializar el almacenamiento Milvus para {user_email}")
    except Exception as e:
        logger.error(f"Error al inicializar Milvus: {e}")
        raise HTTPException(status_code=500, detail="Error al inicializar el sistema de RAG") from e
    
    # Inicializar el agente Zolkin
    try:
        zolkin_agent = ZolkinAgent(
            google_creds=credentials,
            milvus_conn=milvus_conn,
            milvus_storage=milvus_storage,
            partition_key_field=user_email,
        )
        
        # Inicializar herramientas
        zolkin_agent = zolkin_agent.init_tools()
        # Guardar la instancia de ZolkinAgent en el gestor de agentes
        agent_manager.set_zolkin(user_email, zolkin_agent)
        logger.info(f"Agente Zolkin inicializado para {user_email}")
        
        # Inicializar memoria del agente
        redis_conn = get_redis_conn()
        memory = RedisSaver(redis_conn)
        # Crear el agente con memoria
        agent = zolkin_agent.create_agent(memory)
        # Store the LangGraph agent in the agent manager
        agent_manager.set_agent(user_email, agent)
        logger.info(f"Agente configurado para: {user_email}")
    except Exception as e:
        logger.error(f"Error al inicializar el agente Zolkin: {e}")
        raise HTTPException(status_code=500, detail="Error al inicializar el asistente") from e
