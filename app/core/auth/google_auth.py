"""
Functionalities for Google authentication and token management.
"""
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta, UTC

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def get_google_creds(
    token_file: Path, token_data: Dict[str, Any], scopes: List[str]
) -> Credentials:
    """
    Get Google credentials from token data and generate a token file.

    Args:
        token_file (str): The path to the token file.
        token_data (Dict[str, Any]): The token data to use for authentication.
        scopes (List[str]): The scopes to use for authentication.

    Returns:
        Credentials: The Google credentials object.
    """
    creds = None
    if token_file.exists():
        # Borrar el archivo de token si ya existe, por si ha caducado
        token_file.unlink()
    # Generar el token file de nuevo
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
        expiry=datetime.now(UTC) + timedelta(seconds=token_data.get("expires_in")),
    )
    with open(token_file, "w", encoding="utf-8") as file:
        file.write(creds.to_json())
    return creds
