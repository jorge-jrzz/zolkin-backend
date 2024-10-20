"""Get the events in Google Calendar."""


from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun

from pydantic import BaseModel, Field

from pytz import timezone

from tools.calendar.base import GoogleCalendarBaseTool


def get_current_datetime() -> str:
        """Get the current datetime."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class GetEventsSchema(BaseModel):
    """Input for CalendarGetEvents."""

    min_datetime: Optional[str] = Field(
        default=get_current_datetime(),
        description=("The start datetime for the events in 'YYYY-MM-DD HH:MM:SS' format"
                     "The current year is 2024")
    )
    max_datetime: Optional[str] = Field(
        ...,
        description="The end datetime for the events in 'YYYY-MM-DD HH:MM:SS' format",
    )
    max_results: int = Field(
        default=10,
        description="The maximum number of results to return."
    )
    

class CalendarGetEvents(GoogleCalendarBaseTool):
    """Tool that get the events in Google Calendar."""
    name: str = "get_events"
    description: str = "Use this tool to list the events in the calendar."
    args_schema: Type[GetEventsSchema] = GetEventsSchema


    def __get_calendars_info(self) -> List[Any]:
        """Get the calendars info."""
        calendars = self.api_resource.calendarList().list().execute()
        return calendars['items']
    
    def __get_calendar_timezone(self, calendars_info: List, calendar_id: str) -> Optional[str]:
        """Get the timezone of the current calendar."""
        for cal in calendars_info:
            if cal['id'] == calendar_id:
                return cal['timeZone']
        return None

    def __get_calendars(self, calendars_info: List) -> List[str]:
        """Get the calendars IDs."""
        calendars = []
        for cal in calendars_info:
            if cal.get('selected', None):
                calendars.append(cal['id'])
        return calendars
    
    def _process_data_events(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Process the data events."""
        simplified_data = []
        for data in events_data:
            # Extract relevant fields
            event_dict = {
            "id": data["id"],
            "htmlLink": data["htmlLink"],
            "summary": data["summary"],
            "creator": data["creator"]["email"],
            "organizer": data["organizer"]["email"],
            "start": data["start"]["dateTime"],
            "end": data["end"]["dateTime"],
            }
            simplified_data.append(event_dict)
        return simplified_data
    
    def _run(
        self,
        min_datetime: Optional[str],
        max_datetime: Optional[str] = None,
        max_results: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[Dict[str, str]]:
        """Run the tool."""
        try:
            # body_request = self._prepare_request(min_datetime, max_datetime, max_results)
            calendars_info = self.__get_calendars_info()
            calendars = self.__get_calendars(calendars_info)
            events = []
            timeMin = None
            timeMax = None
            for calendar in calendars:
                region_tz = timezone(self.__get_calendar_timezone(calendars_info, calendar))
                if min_datetime:
                    timeMin = region_tz.localize(datetime.strptime(min_datetime, "%Y-%m-%d %H:%M:%S")).isoformat()
                if max_datetime:
                    timeMax = region_tz.localize(datetime.strptime(max_datetime, "%Y-%m-%d %H:%M:%S")).isoformat()
                events_result = self.api_resource.events().list(
                    calendarId=calendar, 
                    timeMin=timeMin, 
                    timeMax=timeMax, 
                    maxResults=max_results, 
                    singleEvents=True, 
                    orderBy="startTime"
                ).execute()
                cal_events = events_result.get('items', [])
                events.extend(cal_events)
            return self._process_data_events(events)
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
