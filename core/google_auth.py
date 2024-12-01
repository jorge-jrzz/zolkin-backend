import os
from typing import Dict, List, Any

from datetime import datetime, timedelta, UTC
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_google_creds(token_file, token_data: Dict[str, Any], scopes: List[str]) -> Credentials:
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:         
                creds = Credentials(
                    token = token_data['access_token'],
                    refresh_token = token_data['refresh_token'],
                    client_id = os.getenv('GOOGLE_CLIENT_ID'),
                    client_secret = os.getenv('GOOGLE_CLIENT_SECRET'),
                    token_uri = "https://oauth2.googleapis.com/token",
                    scopes = scopes,
                    expiry = datetime.now(UTC) + timedelta(seconds=token_data['expires_in']),
                )
            with open(token_file, "w", encoding="utf-8") as file:
                file.write(creds.to_json())
    return creds
            