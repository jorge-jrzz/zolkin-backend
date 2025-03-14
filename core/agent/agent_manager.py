"""Agent manager utilities."""
from typing import Dict, Any

from core.agent import ZolkinAgent


# Caché global para almacenar instancias de agentes por usuario
agent_cache: Dict[str, Any] = {}
# Caché para almacenar las instancias originales de ZolkinAgent
zolkin_cache: Dict[str, ZolkinAgent] = {}

def get_agent(email: str) -> Any:
    """Obtiene el agente para un usuario desde la caché."""
    return agent_cache.get(email)


def set_agent(email: str, agent: Any) -> None:
    """Almacena un agente en la caché para un usuario."""
    agent_cache[email] = agent


def remove_agent(email: str) -> None:
    """Elimina un agente de la caché."""
    agent_cache.pop(email, None)


def get_zolkin(email: str) -> ZolkinAgent:
    """Obtiene la instancia original de ZolkinAgent para un usuario."""
    return zolkin_cache.get(email)


def set_zolkin(email: str, zolkin: ZolkinAgent) -> None:
    """Almacena una instancia original de ZolkinAgent en la caché."""
    zolkin_cache[email] = zolkin


def remove_zolkin(email: str) -> None:
    """Elimina una instancia de ZolkinAgent de la caché."""
    zolkin_cache.pop(email, None)
