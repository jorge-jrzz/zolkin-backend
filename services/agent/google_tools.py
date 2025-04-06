"""
Tools para el agente de IA - Integración con Google APIs y Milvus para RAG.
Este módulo proporciona herramientas para interactuar con Gmail, Google Calendar
y un sistema de RAG basado en Milvus.
"""
import logging
from typing import List, Any

from langchain_core.tools import BaseTool
from google.oauth2.credentials import Credentials
from langchain_google_community import GmailToolkit, CalendarToolkit
from langchain_google_community.calendar.utils import build_resource_service


logger = logging.getLogger(__name__)


def get_gmail_toolkit(api_resource: Any) -> List[BaseTool]:
    """
    Obtiene las herramientas de Gmail.
    
    Args:
        api_resource: Recurso de API de Gmail
        
    Returns:
        Lista de herramientas de Gmail
    """
    try:
        toolkit = GmailToolkit(api_resource=api_resource)
        tools = toolkit.get_tools()
        logger.info(f"Obtenidas {len(tools)} herramientas de Gmail")
        return tools
    except Exception as e:
        logger.error(f"Error obteniendo herramientas de Gmail: {e}")
        return []


def get_calendar_toolkit(api_resource: Any) -> List[BaseTool]:
    """
    Obtiene las herramientas de Google Calendar.
    
    Args:
        api_resource: Recurso de API de Calendar
        
    Returns:
        Lista de herramientas de Calendar
    """
    try:
        toolkit = CalendarToolkit(api_resource=api_resource)
        tools = toolkit.get_tools()
        logger.info(f"Obtenidas {len(tools)} herramientas de Calendar")
        return tools
    except Exception as e:
        logger.error(f"Error obteniendo herramientas de Calendar: {e}")
        return []


def get_google_toolkit(credentials: Credentials) -> List[Any]:
    """
    Obtiene todas las herramientas de Google (Gmail y Calendar).
    
    Args:
        credentials: Credenciales de OAuth2 de Google
        
    Returns:
        Lista combinada de herramientas de Gmail y Calendar
    """
    try:
        # Construir recursos de API
        gmail_resource = build_resource_service(
            credentials=credentials, service_name="gmail", service_version="v1"
        )
        calendar_resource = build_resource_service(
            credentials=credentials, service_name="calendar", service_version="v3"
        )
        
        # Obtener toolkits
        gmail_toolkit = get_gmail_toolkit(api_resource=gmail_resource)
        calendar_toolkit = get_calendar_toolkit(api_resource=calendar_resource)
        
        # Combinar herramientas
        all_tools = gmail_toolkit + calendar_toolkit
        logger.info(f"Toolkit de Google completo creado con {len(all_tools)} herramientas")
        return all_tools
    except Exception as e:
        logger.error(f"Error creando toolkit de Google: {e}")
        return []
