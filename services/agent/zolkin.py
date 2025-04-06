"""
ZolkinAgent - Agente de inteligencia artificial con integración de servicios Google y RAG.
Esta clase implementa un agente basado en LangGraph capaz de utilizar herramientas de Google
y recuperación de información a través de un sistema RAG con Milvus.
"""
import os
import logging
from typing import Any, List, Set, Optional
from typing_extensions import Self

from langchain_milvus import Milvus
from langchain_core.tools import Tool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pymilvus import Collection, connections
from google.oauth2.credentials import Credentials
from langgraph.prebuilt import create_react_agent

from .memory import RedisSaver
from .milvus_storage import MilvusStorage
from .google_tools import get_google_toolkit


logger = logging.getLogger(__name__)


class ZolkinAgent:
    """
    Agente de IA que integra herramientas de Google y RAG con Milvus.
    
    Esta clase proporciona un agente capaz de utilizar herramientas de Gmail,
    Google Calendar y un sistema de RAG basado en Milvus para responder
    consultas de los usuarios y realizar acciones en sus cuentas.
    """

    def __init__(
        self,
        google_creds: Credentials,
        milvus_conn: MilvusStorage,
        milvus_storage: Milvus,
        partition_key_field: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        """
        Inicializa el agente Zolkin.
        
        Args:
            google_creds: Credenciales de Google OAuth2
            milvus_conn: Conexión a Milvus
            milvus_storage: Almacenamiento de vectores Milvus
            partition_key_field: Campo de partición (típicamente el email del usuario)
            model_name: Nombre del modelo a utilizar (por defecto usa OPENAI_MODEL de env)
            api_key: API key para el modelo (por defecto usa OPENAI_API_KEY de env)
            system_message: Mensaje de sistema personalizado
        """
        self.google_creds = google_creds
        self.milvus_conn = milvus_conn
        self.milvus_storage = milvus_storage
        self.partition_key_field = partition_key_field
        self._model = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0.2  # Temperatura más baja para respuestas más consistentes
        )
        self._tools: List[Tool] = []
        self._default_system_message = system_message or (
            "Eres un asistente útil capaz de gestionar el correo electrónico y calendario del usuario. "
            "También puedes encontrar información valiosa usando la herramienta RAG. "
            "Responde siempre en el mismo idioma que utilice el usuario. "
            "Si necesitas información adicional para completar una tarea, pregúntale al usuario de manera clara y directa."
        )
        self._agent = None
        
    def _create_rag_tool(self) -> List[Tool]:
        """
        Crea la herramienta de RAG basada en Milvus.
        
        Returns:
            Lista con la herramienta de RAG
        """
        try:
            rag_tool = self.milvus_conn.create_retriever_tool(
                self.milvus_storage, self.partition_key_field
            )
            if rag_tool:
                # Actualizar descripción con información de los archivos disponibles
                collection_name = self.milvus_storage.collection_name
                files = self._get_unique_filenames(self.partition_key_field, collection_name)
                if files:
                    file_list = ", ".join(sorted(files))
                    rag_tool.description = (
                        f"Busca información en los documentos del usuario. "
                        f"Documentos disponibles: {file_list}. "
                        f"Usa esta herramienta cuando necesites información específica de estos documentos."
                    )
                return [rag_tool]
            else:
                logger.warning("No se pudo crear la herramienta RAG")
                return []
        except Exception as e:
            logger.error(f"Error al crear herramienta RAG: {e}")
            return []

    def _create_google_tools(self) -> List[Any]:
        """
        Crea las herramientas de Google (Gmail y Calendar).
        
        Returns:
            Lista de herramientas de Google
        """
        try:
            return get_google_toolkit(self.google_creds)
        except Exception as e:
            logger.error(f"Error al crear herramientas de Google: {e}")
            return []

    def _get_unique_filenames(self, namespace: str, collection_name: str) -> Set[str]:
        """
        Obtiene los nombres únicos de archivos almacenados en Milvus para un namespace.
        
        Args:
            namespace: Namespace del usuario (típicamente email)
            collection_name: Nombre de la colección en Milvus
            
        Returns:
            Conjunto de nombres de archivos únicos
        """
        try:
            connections.connect("default", uri=os.getenv("MILVUS_URL", "http://localhost:19530"))
            collection = Collection(collection_name)
            collection.load()
            results = collection.query(
                expr=f"namespace == '{namespace}'", output_fields=["source"]
            )
            names = [r["source"] for r in results if r.get("source")]
            connections.disconnect("default")
            return set(names)
        except Exception as e:
            logger.error(f"Error al obtener nombres de archivos: {e}")
            return set()

    def update_rag_tool_description(self) -> None:
        """
        Actualiza la descripción de la herramienta RAG con los archivos disponibles.
        """
        collection_name = self.milvus_storage.collection_name
        for tool in self._tools:
            if isinstance(tool, Tool) and (tool.name == "Milvus_RAG" or tool.name == "buscar_informacion"):
                files = self._get_unique_filenames(self.partition_key_field, collection_name)
                if files:
                    file_list = ", ".join(sorted(files))
                    tool.description = (
                        f"Busca información en los documentos del usuario. "
                        f"Documentos disponibles: {file_list}. "
                        f"Usa esta herramienta cuando necesites información específica de estos documentos."
                    )
                else:
                    tool.description = (
                        "Busca información en la base de conocimiento del usuario. "
                        "Actualmente no hay documentos disponibles."
                    )
                logger.info(f"Descripción de herramienta RAG actualizada para {self.partition_key_field}")
                break

    def init_tools(self) -> Self:
        """
        Inicializa todas las herramientas del agente.
        
        Returns:
            Self para encadenamiento de métodos
        """
        # Obtener herramientas de ambas fuentes
        google_tools = self._create_google_tools()
        rag_tools = self._create_rag_tool()
        
        # Asegurar que todas las herramientas sean objetos Tool válidos
        self._tools = []
        all_tools = google_tools + rag_tools
        
        for tool in all_tools:
            if not hasattr(tool, 'name') or not tool.name:
                logger.warning("Omitiendo herramienta sin nombre")
                continue
                
            self._tools.append(tool)
        
        logger.info(f"Se inicializaron {len(self._tools)} herramientas para el agente")
        return self

    def create_agent(self, memory: RedisSaver) -> Any:
        """
        Crea una instancia del agente LangGraph con todas las herramientas configuradas.
        
        Args:
            memory: Gestor de memoria del agente para persistencia
            
        Returns:
            Agente LangGraph listo para ser utilizado
        """
        # Crear mensaje de sistema
        system_message = SystemMessage(content=self._default_system_message)
        
        # Validar herramientas
        if not self._tools:
            logger.warning("Creando agente sin herramientas")
        else:
            logger.info(f"Creando agente con {len(self._tools)} herramientas:")
            for tool in self._tools:
                logger.info(f"  - {tool.name}: {tool.description[:50]}...")
        
        # Crear el agente con ReAct
        try:
            self._agent = create_react_agent(
                model=self._model,
                tools=self._tools,
                state_modifier=system_message,
                checkpointer=memory,
            )
            logger.info(f"Agente creado exitosamente para {self.partition_key_field}")
            return self._agent
        except Exception as e:
            logger.error(f"Error al crear el agente: {e}")
            raise
