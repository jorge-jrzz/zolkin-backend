"""User manager utilities."""
from typing import Dict


users_cache: Dict[str, Dict[str, str]] = {}

def get_user(email: str) -> Dict[str, str]:
    """Obtiene el usuario desde la caché."""
    return users_cache.get(email)


def set_user(email: str, user: Dict[str, str]) -> None:
    """Almacena un usuario en la caché."""
    users_cache[email] = user
