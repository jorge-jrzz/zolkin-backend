"""Create an event in Google Calendar."""

import re
from uuid import uuid4
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type

from langchain_core.callbacks import CallbackManagerForToolRun

from pydantic import BaseModel, Field

from tools.calendar.base import GoogleCalendarBaseTool


def get_current_datetime() -> str:
        """Get the current datetime."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class CreateEventSchema(BaseModel):
    """Input for CalendarCreateEvent."""

    summary: str = Field(
        ...,
        description="The title of the event.",
    )
    start_datetime: str = Field(
        default=get_current_datetime(),
        description=("The start datetime for the event in 'YYYY-MM-DD HH:MM:SS' format"
                     "The current year is 2024")
    )
    end_datetime: str = Field(
        ...,
        description="The end datetime for the event in 'YYYY-MM-DD HH:MM:SS' format",
    )
    recurrence: Optional[Dict[str, Any]] = Field(
        default=None,
        description=("The recurrence of the event."
                     "The format is"
                     "{'FREQ': <'DAILY' or 'WEEKLY'>,"
                     "'INTERVAL': <number>,"
                     "'COUNT': <number or None>,"
                     "'UNTIL': <'YYYYMMDD' or None>,"
                     "'BYDAY': <'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU' or None>}"
                     "Can be used COUNT or UNTIL, but not both, set the other to None.")
    )
    location: Optional[str] = Field(
        default=None,
        description="The location of the event."
    )
    description: Optional[str] = Field(
        default=None,
        description="The description of the event."
    )
    attendees: Optional[List[str]] = Field(
        delault=None,
        description="The list of attendees for the event."
    )
    reminders: Union[None, bool, List[Dict[str, Any]]] = Field(
        default=None,
        description=("The reminders for the event."
                     "If reminders are needed but are not specific, then set to 'True'"
                     "If specified, then set as [{'method': 'email', 'minutes': <minutes>}]"
                     "Or set as [{'method': 'popup', 'minutes': <minutes>}]"
                     "Where <minutes> is the number of minutes before the event."
                     "60 minutes = 1 hour."
                     "60 * 24 = 1 day."
                     )
    )
    conferenceData: Optional[bool] = Field(
        default=None,
        description="Whether to include conference data."
    )


class CalendarCreateEvent(GoogleCalendarBaseTool):
    """Tool that create a event in Google Calendar."""

    name: str = "create_event"
    description: str = (
        "Use this tool to create an event." 
        "The input must be the summary, start and end datetime for the event."
    )
    args_schema: Type[CreateEventSchema] = CreateEventSchema

    def __get_timeZone(self) -> str:
        """Get the timezone of the primary calendar."""
        calendars = self.api_resource.calendarList().list().execute()
        return calendars['items'][0]['timeZone']

    def _prepare_event(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        recurrence: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None, 
        attendees: Optional[List[str]] = None,
        reminders: Union[None, bool, List[Dict[str, Any]]] = None,
        conferenceData: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Prepare the event body."""
        try: 
            date_object = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
            start = date_object.astimezone().replace(microsecond=0).isoformat()
            date_object = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
            end = date_object.astimezone().replace(microsecond=0).isoformat()
        except ValueError:
            raise ValueError("The datetime format is incorrect. Please use 'YYYY-MM-DD HH:MM:SS' format.")
        timezone = self.__get_timeZone()
        recurrence_data = None
        if recurrence:
            if isinstance(recurrence, dict):
                recurrence_data = ['RRULE:']
                print(recurrence, "\n\n\n")
                for k, v in recurrence.items():
                    if v is not None:
                        recurrence_data.append(f"{k}={v};")
                recurrence_data = ''.join(recurrence_data)

        attendees_mails = []
        if attendees and isinstance(attendees, list):
            for attendee in attendees:
                valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', attendee)
                if not valid:
                    raise ValueError(f"Invalid email address: {attendee}")
                attendees_mails.append({"email": attendee})
        reminders_info = None
        if reminders: 
            if reminders is True:
                reminders_info = {"useDefault": True}
            elif isinstance(reminders, list):
                for reminder in reminders:
                    if 'method' not in reminder or 'minutes' not in reminder:
                        raise ValueError("The reminders must have 'method' and 'minutes' keys.")
                    if reminder['method'] not in ['email', 'popup']:
                        raise ValueError("The reminders method must be 'email' or 'popup'.")
                reminders_info = {
                    'useDefault': False,
                    "overrides": reminders 
                }
        else:
            reminders_info = {"useDefault": False}
        if conferenceData:
            conferenceData = {
                "createRequest": {
                    "requestId": str(uuid4()),
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }
        
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
            "recurrence": [recurrence_data], 
            "attendees": attendees_mails, 
            "reminders": reminders_info,
            "conferenceData": conferenceData
        }
        return event
    
    def _run(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        recurrence: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Union[None, bool, List[Dict[str, Any]]] = None,
        conferenceData: Optional[bool] = None, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Run the tool."""
        try:
            body = self._prepare_event(summary, 
                                       start_datetime, 
                                       end_datetime, 
                                       recurrence=recurrence,
                                       location=location, 
                                       description=description, 
                                       attendees=attendees, 
                                       reminders=reminders,
                                       conferenceData=conferenceData)
            
            conferenceVersion = 1 if conferenceData else 0
            event = self.api_resource.events().insert(calendarId='primary', 
                                                      body=body, 
                                                      conferenceDataVersion=conferenceVersion).execute()
            return event.get('htmlLink')
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
