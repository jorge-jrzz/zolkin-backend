"""Google Calendar Toolkit."""
from typing import Any, List

from langchain_google_community import CalendarToolkit


def get_calendar_toolkit(api_resource: Any) -> List[Any]:
    toolkit = CalendarToolkit(api_resource=api_resource)
    return toolkit.get_tools()
