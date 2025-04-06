"""
AgentManager Class to manage agent instances for users.
This class provides a singleton to manage agent instances for multiple users,
avoiding unnecessary recreation.
"""
import logging
from typing import Any, Dict, Optional

from .zolkin import ZolkinAgent


logger = logging.getLogger(__name__)


class AgentManager:
    """
    Administrador de instancias de agentes por usuario.
    
    Esta clase proporciona un singleton para gestionar las instancias
    de agentes para múltiples usuarios, evitando recrearlos innecesariamente.
    """
    
    _instance: Optional['AgentManager'] = None
    
    def __new__(cls) -> 'AgentManager':
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance._agent_cache: Dict[str, Any] = {}
            cls._instance._zolkin_cache: Dict[str, ZolkinAgent] = {}
        return cls._instance
    
    def get_agent(self, email: str) -> Optional[Any]:
        """
        Obtiene el agente para un usuario desde la caché.
        
        Args:
            email: Email del usuario
            
        Returns:
            Instancia del agente o None si no existe
        """
        return self._agent_cache.get(email)
    
    def set_agent(self, email: str, agent: Any) -> None:
        """
        Almacena un agente en la caché para un usuario.
        
        Args:
            email: Email del usuario
            agent: Instancia del agente
        """
        self._agent_cache[email] = agent
        logger.info(f"Agente almacenado en caché para {email}")
    
    def get_zolkin(self, email: str) -> Optional[ZolkinAgent]:
        """
        Obtiene la instancia original de ZolkinAgent para un usuario.
        
        Args:
            email: Email del usuario
            
        Returns:
            Instancia de ZolkinAgent o None si no existe
        """
        return self._zolkin_cache.get(email)
    
    def set_zolkin(self, email: str, zolkin: ZolkinAgent) -> None:
        """
        Almacena una instancia original de ZolkinAgent en la caché.
        
        Args:
            email: Email del usuario
            zolkin: Instancia de ZolkinAgent
        """
        self._zolkin_cache[email] = zolkin
        logger.info(f"Instancia ZolkinAgent almacenada para {email}")
