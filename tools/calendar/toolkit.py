from __future__ import annotations

from typing import TYPE_CHECKING, List
from pydantic import ConfigDict, Field

from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_core.tools import BaseTool
from langchain_google_community.gmail.utils import build_resource_service

from tools.calendar.create_event import CalendarCreateEvent
from tools.calendar.get_events import CalendarGetEvents

if TYPE_CHECKING:
    # This is for linting and IDE typehints
    from googleapiclient.discovery import Resource  # type: ignore[import]
else:
    try:
        # We do this so pydantic can resolve the types when instantiating
        from googleapiclient.discovery import Resource
    except ImportError:
        pass


SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarToolkit(BaseToolkit):
    """Toolkit for interacting with GoogleCalendar."""

    api_resource: Resource = Field(default_factory=build_resource_service)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        return [
            CalendarCreateEvent(api_resource=self.api_resource),
            CalendarGetEvents(api_resource=self.api_resource)
        ]