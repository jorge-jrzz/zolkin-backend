from .gmail import get_gmail_toolkit
from .calendar import get_calendar_toolkit
from typing import List, Any
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)


__all__ = ["get_agent_toolkit"]


SCOPES = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"]

def build_service(scopes: List[str], 
                  token_file: str = "./secrets/token.json", 
                  client_secrets_file: str = "./secrets/credentials.json") -> Any:
    
    credentials = get_gmail_credentials(
        token_file=token_file, scopes=scopes, client_secrets_file=client_secrets_file
    )
    return build_resource_service(credentials=credentials)

def get_agent_toolkit() -> List[Any]:
    api_resource = build_service(scopes=SCOPES)
    gmail_toolkit = get_gmail_toolkit(api_resource=api_resource)
    calendar_toolkit = get_calendar_toolkit(api_resource=api_resource)
    return gmail_toolkit + calendar_toolkit



