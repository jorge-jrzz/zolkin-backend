"""Agent manager utils."""
from typing import Dict

from core.agent import ZolkinAgent


# Caché global para almacenar instancias de agentes por usuario
agent_cache: Dict[str, ZolkinAgent] = {}

def get_agent(email: str) -> ZolkinAgent:
    """Obtiene el agente para un usuario desde la caché."""
    return agent_cache.get(email)


def set_agent(email: str, agent: ZolkinAgent) -> None:
    """Almacena un agente en la caché para un usuario."""
    agent_cache[email] = agent


def remove_agent(email: str) -> None:
    """Elimina un agente de la caché."""
    agent_cache.pop(email, None)
