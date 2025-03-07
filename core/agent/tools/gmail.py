"""Gmail tools."""
from typing import Any, List

from langchain_google_community import GmailToolkit


def get_gmail_toolkit(api_resource: Any) -> List[Any]:
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit.get_tools()
