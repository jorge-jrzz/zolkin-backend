from typing import Any, List

from google.oauth2.credentials import Credentials
from langchain_community.tools.gmail.utils import (
    build_resource_service, 
    get_gmail_credentials
)

from .calendar import get_calendar_toolkit
from .gmail import get_gmail_toolkit
from .rag import MilvusStorage


__all__ = ["get_google_credentials", "get_google_toolkit", "MilvusStorage"]


def get_google_credentials(token_file: str, scopes: List[str], credentials_file: str) -> Credentials:
    return get_gmail_credentials(
        token_file = token_file,
        scopes = scopes,
        client_secrets_file = credentials_file,
    )


def get_google_toolkit(credentials: Credentials) -> List[Any]:
    gmail_resource = build_resource_service(credentials=credentials)
    calendar_resource = build_resource_service(credentials=credentials, service_name="calendar", service_version="v3")
    gmail_toolkit = get_gmail_toolkit(api_resource=gmail_resource)
    calendar_toolkit = get_calendar_toolkit(api_resource=calendar_resource)
    return gmail_toolkit + calendar_toolkit

def get_rag_tool(collection_name: str) -> MilvusStorage:
    return MilvusStorage(collection_name=collection_name)
