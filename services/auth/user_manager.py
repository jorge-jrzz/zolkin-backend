"""
User management utilities for authentication and session handling.
"""
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class UserManager:
    """
    Manager for user data and sessions.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance._users: Dict[str, Dict[str, Any]] = {}
        return cls._instance
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by ID.
        
        Args:
            user_id (str): User identifier (typically email)
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        return self._users.get(user_id)
    
    def set_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """
        Store or update user data.
        
        Args:
            user_id (str): User identifier (typically email)
            user_data (Dict[str, Any]): User data to store
        """
        self._users[user_id] = user_data
        logger.info(f"User data updated for {user_id}")
