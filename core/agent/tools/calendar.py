from typing import Any, List
from langchain_community.agent_toolkits import GoogleCalendarToolkit


def get_calendar_toolkit(api_resource: Any) -> List[Any]:
    toolkit = GoogleCalendarToolkit(api_resource=api_resource)
    return toolkit.get_tools()
