"""
Functionalities for Google authentication and token management.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError


logger = logging.getLogger(__name__)


class GoogleAuthManager:
    """
    Manager for Google authentication and token management.
    """
    
    def __init__(self, token_dir: Optional[str] = None):
        """
        Initialize the Google Authentication Manager.
        
        Args:
            token_dir (Optional[str]): Directory to store token files. If None, uses a default directory.
        """
        self.token_dir = Path(token_dir) if token_dir else Path(os.getenv("TOKENS_DIR", "./tokens"))
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    def get_token_path(self, user_id: str) -> Path:
        """
        Get the path to the token file for a specific user.
        
        Args:
            user_id (str): User identifier (typically email)
            
        Returns:
            Path: Path to the token file
        """
        # Sanitize user_id to create a valid filename
        safe_id = user_id.split("@")[0]
        return self.token_dir / f"{safe_id}_token.json"
    
    def create_credentials(
        self, 
        token_data: Dict[str, Any], 
        scopes: Optional[List[str]]
    ) -> Credentials:
        """
        Create Google credentials from token data.
        
        Args:
            token_data (Dict[str, Any]): The token data from OAuth flow
            scopes (Optional[List[str]]): The scopes to use for authentication
            
        Returns:
            Credentials: The Google credentials object
            
        Raises:
            ValueError: If required token data is missing
        """
        if not token_data.get("access_token"):
            raise ValueError("Access token is required")
            
        if not self.client_id or not self.client_secret:
            raise ValueError("Google client ID and secret must be set in environment variables")

        # Create credentials
        return Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
        )
    
    def save_credentials(self, credentials: Credentials, user_id: str) -> Path:
        """
        Save credentials to a token file.
        
        Args:
            credentials (Credentials): The credentials to save
            user_id (str): User identifier (typically email)
            
        Returns:
            Path: Path to the saved token file
        """
        token_file = self.get_token_path(user_id)
        
        try:      
            # Save credentials to file
            with open(token_file, "w", encoding="utf-8") as file:
                file.write(credentials.to_json())
                
            logger.info(f"Credentials saved for user {user_id} at {token_file}")
            return token_file
        except Exception as e:
            logger.error(f"Error saving credentials for user {user_id}: {e}")
            raise
