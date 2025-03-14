"""Core module for Zolkin project."""
from .agent.memory import RedisSaver
from .processing.ocr import LoadFile
from .agent.tools import MilvusStorage
from .auth.google_auth import get_google_creds
from .auth.user_manager import users_cache, get_user, set_user
from .processing.files_strategy import manage_files
from .agent import (
    ZolkinAgent,
    agent_cache,
    get_agent,
    set_agent,
    remove_agent,
    zolkin_cache,
    set_zolkin,
    remove_zolkin,
    get_zolkin
)

__all__ = [
    "get_google_creds",
    "manage_files",
    "LoadFile",
    "ZolkinAgent",
    "MilvusStorage",
    "RedisSaver",
    "agent_cache",
    "get_agent",
    "set_agent",
    "remove_agent",
    "zolkin_cache",
    "set_zolkin",
    "remove_zolkin",
    "get_zolkin", 
    "users_cache",
    "get_user",
    "set_user"
]
