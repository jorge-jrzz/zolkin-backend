"""Tools for Google APIs and RAG."""
from typing import Any, List

from google.oauth2.credentials import Credentials
from langchain_google_community.calendar.utils import build_resource_service

from .calendar import get_calendar_toolkit
from .gmail import get_gmail_toolkit
from .rag import MilvusStorage


__all__ = ["get_google_toolkit", "MilvusStorage"]


def get_google_toolkit(credentials: Credentials) -> List[Any]:
    """Get Google toolkit."""
    gmail_resource = build_resource_service(
        credentials=credentials, service_name="gmail", service_version="v1"
    )
    calendar_resource = build_resource_service(credentials=credentials)
    gmail_toolkit = get_gmail_toolkit(api_resource=gmail_resource)
    calendar_toolkit = get_calendar_toolkit(api_resource=calendar_resource)
    return gmail_toolkit + calendar_toolkit
