import json
from datetime import datetime as datetime_datetime, timezone
from typing import cast, List

from googleapi.Helpers.HelperFunctions import build_service_account_credentials, execute_aiogoogle
from googleapi.TypedDicts.Calendar import (
    CalendarListModel,
    CalendarListEntryModel,
    CalendarModel,
    EventsModel,
    EventModel,
    AclRuleModel,
    AclModel,
)


class Calendar:
    """
    Implements the Google Calendar API to add events to calendars
    """

    def __init__(self, service_file: json, subject: str) -> None:
        """
        @param service_file: Service account credentials file
        @param subject: Subject who owns the calendar
        """
        self.timeZone = "Europe/Brussels"

        self.service_account_credentials = build_service_account_credentials(service_file=service_file, scopes=["https://www.googleapis.com/auth/calendar"], subject=subject)
        self.api_name = "calendar"
        self.api_version = "v3"

    def _build_event_body(
        self,
        title: str,
        description: str,
        location: str,
        start_time: datetime_datetime,
        end_time: datetime_datetime,
    ) -> EventModel:
        """
        Used to build the body of an event in the form that Google Calendar API accepts
        @param title: Title of the event
        @param description: Description of the event
        @param location: Location of the event
        @param start_time: Start time of the event in isoformat
        @param end_time: End time of the event in isoformat
        @return: Dictionary of type EventModel that Google Calendar API accepts
        """
        eventBody = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": self.timeZone},
            "end": {"dateTime": end_time.isoformat(), "timeZone": self.timeZone},
        }
        return cast(EventModel, eventBody)

    def _build_calendar_body(
        self, title: str, location: str, description: str
    ) -> CalendarModel:
        """
        Used to build the body of a calendar in the form that Google Calendar API accepts
        @param title: Title of the calendar
        @param location: Location of the calendar
        @param description: Description of the calendar
        @return: Dictionary of type CalendarModel that Google Calendar API accepts
        """
        calendarBody = {
            "summary": title,
            "location": location,
            "description": description,
            "timeZone": self.timeZone,
        }
        return cast(CalendarModel, calendarBody)

    def _build_scope_body(
        self, scope_type: str, scope_value: str, role: str
    ) -> AclRuleModel:
        """
        Used to build the body of an acl scope in the form that Google Calendar API accepts
        @param scope_type: Type of the scope
        @param scope_value: Value of the scope
        @param role: Role of the scope
        @return: Dictionary of type AclRuleModel that Google Calendar API accepts
        """
        rule = {"scope": {"type": scope_type, "value": scope_value}, "role": role}
        return cast(AclRuleModel, rule)

    async def add_event(
        self,
        calendar_id: str,
        title: str,
        start_time: datetime_datetime,
        end_time: datetime_datetime,
        description: str = "",
        location: str = "",
    ) -> EventModel:
        """
        Adds an event to the calendar
        @param calendar_id: ID of the calendar that the event needs to be added to
        @param title: Title of the event
        @param start_time: Start time of the event in isoformat
        @param end_time: End time of the event
        @param description: Optional description of the event
        @param location: Optional location of the event
        @return: The created event
        """
        eventBody = self._build_event_body(
            title, description, location, start_time, end_time
        )
        method_callable = lambda calendar, **kwargs: calendar.events.insert(**kwargs)
        method_args = {"calendarId": calendar_id, "body": eventBody}
        return cast(
            EventModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def get_events(
        self, calendar_id: str, get_all_events: bool = False
    ) -> List[EventsModel]:
        """
        Get all events in the calendar
        @param calendar_id: ID of the calendar
        @param get_all_events: Whether to return all events or only after the current date
        @return: Returns all the events in the calendar
        """
        method_callable = lambda calendar, **kwargs: calendar.events.list(**kwargs)
        if get_all_events:
            method_args = {
                "calendarId": calendar_id,
                "orderBy": "startTime",
                "singleEvents": True,
            }
        else:
            currentTime = datetime_datetime.now(timezone.utc).isoformat()
            method_args = {
                "calendarId": calendar_id,
                "orderBy": "startTime",
                "singleEvents": True,
                "timeMin": currentTime,
            }
        return cast(
            EventsModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        ).get("items", [])

    async def get_event(self, calendar_id: str, event_id: str) -> EventModel:
        """
        Returns the event of the calendar
        @param calendar_id: ID of the calendar the event is in
        @param event_id: ID of the event
        @return: The event
        """
        method_callable = lambda calendar, **kwargs: calendar.events.get(**kwargs)
        method_args = {"calendarId": calendar_id, "eventId": event_id}
        return cast(
            EventModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def remove_event(self, event_id: str, calendar_id: str) -> None:
        """
        Removes an event from the calendar
        @param event_id: ID of the event that needs to be removed
        @param calendar_id: ID of the calendar the event is in
        @return: Nothing
        """
        method_callable = lambda calendar, **kwargs: calendar.events.delete(**kwargs)
        method_args = {"calendarId": calendar_id, "eventId": event_id}
        await execute_aiogoogle(method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args)

    async def update_event(
        self,
        event_id: str,
        calendar_id: str,
        title: str = None,
        start_time: datetime_datetime = None,
        end_time: datetime_datetime = None,
        description: str = None,
        location: str = None,
    ) -> EventModel:
        """
        Updates an event of the calendar
        @param event_id: ID of the event that needs to be updated
        @param calendar_id: ID of the calendar the event is in
        @param title: Optional title of the event
        @param start_time: Optional start time of the event in isoformat
        @param end_time: Optional end time of the event in isoformat
        @param description: Optional description of the event
        @param location: Optional location of the event
        @return: The updated event
        """
        if all(x is None for x in [title, start_time, end_time, description, location]):
            raise Exception("Update arguments don't have a value")

        oldEvent = await self.get_event(calendar_id=calendar_id, event_id=event_id)

        currentTitle = oldEvent["summary"]
        currentStartTime = oldEvent["start"]["dateTime"]
        currentEndTime = oldEvent["end"]["dateTime"]
        currentDescription = oldEvent["description"]
        currentLocation = oldEvent["location"]

        if title is None:
            title = currentTitle
        if start_time is None:
            start_time = currentStartTime
        if end_time is None:
            end_time = currentEndTime
        if description is None:
            description = currentDescription
        if location is None:
            location = currentLocation

        if (
            title == currentTitle
            and start_time == currentStartTime
            and end_time == currentEndTime
            and description == currentDescription
            and location == currentLocation
        ):
            raise Exception("Not a single parameter gets a new value")

        newEventBody = self._build_event_body(
            title, description, location, start_time, end_time
        )

        method_callable = lambda calendar, **kwargs: calendar.events.update(**kwargs)
        method_args = {
            "calendarId": calendar_id,
            "eventId": event_id,
            "body": newEventBody,
        }
        return cast(
            EventModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def move_event(
        self, event_id: str, old_calendar_id: str, new_calendar_id: str
    ) -> EventModel:
        """
        Moves an event to the new calendar
        @param event_id: ID of the event that needs to be moved
        @param old_calendar_id: ID of the calendar is currently in
        @param new_calendar_id: ID of the calendar the event is moved to
        @return: The moved event
        """
        method_callable = lambda calendar, **kwargs: calendar.events.move(**kwargs)
        method_args = {
            "calendarId": old_calendar_id,
            "eventId": event_id,
            "destination": new_calendar_id,
        }
        return cast(
            EventModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def add_calendar(
        self, title: str, location: str = "", description: str = ""
    ) -> CalendarModel:
        """
        Adds a calendar
        @param title: Title of the calendar
        @param location: Optional geographical location of the calendar
        @param description: Optional description of the calendar
        @return: The created calendar
        """
        calendarBody = self._build_calendar_body(title, location, description)
        method_callable = lambda calendar, **kwargs: calendar.calendars.insert(**kwargs)
        method_args = {"body": calendarBody}
        return cast(
            CalendarModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def get_calendars(self) -> List[CalendarListEntryModel]:
        """
        Returns all the calendars of the user
        @return: All the calendars of the user
        """
        method_callable = lambda calendar, **kwargs: calendar.calendarList.list()
        return cast(
            CalendarListModel,
            await execute_aiogoogle(method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version),
        ).get("items", [])

    async def get_calendar(self, calendar_id: str) -> CalendarModel:
        """
        Returns the calendar of the user
        @param calendar_id: ID of the calendar
        @return: Returns the calendar
        """
        method_callable = lambda calendar, **kwargs: calendar.calendars.get(**kwargs)
        method_args = {"calendarId": calendar_id}
        return cast(
            CalendarModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def update_calendar(
        self,
        calendar_id: str,
        title: str = None,
        location: str = None,
        description: str = None,
    ) -> CalendarModel:
        """
        Updates the calendar
        @param calendar_id: ID of the calendar that needs to be updated
        @param title: Title of the calendar
        @param location: Optional geographical location of the calendar
        @param description: Optional description of the calendar
        @return: The updated calendar
        """
        if all(x is None for x in [title, description, location]):
            raise Exception("Not a single argument is updated")

        oldCalendar = await self.get_calendar(calendar_id=calendar_id)

        currentTitle = oldCalendar["summary"]
        currentDescription = oldCalendar["description"]
        currentLocation = oldCalendar["location"]

        if title is None:
            title = currentTitle
        if description is None:
            description = currentDescription
        if location is None:
            location = currentLocation

        if (
            title == currentTitle
            and description == currentDescription
            and location == currentLocation
        ):
            raise Exception("Not a single parameter gets a new value")

        newCalendarBody = self._build_calendar_body(title, location, description)
        method_callable = lambda calendar, **kwargs: calendar.calendars.update(**kwargs)
        method_args = {"calendarId": calendar_id, "body": newCalendarBody}
        return cast(
            CalendarModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def remove_calendar(self, calendar_id: str) -> None:
        """
        Removes the calendar
        @param calendar_id: ID of the calendar to be removed
        @return: Nothing
        """
        method_callable = lambda calendar, **kwargs: calendar.calendars.delete(**kwargs)
        method_args = {"calendarId": calendar_id}
        await execute_aiogoogle(method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args)

    async def clear_calendar(self, calendar_id: str) -> None:
        """
        Removes all the events in the calendar
        @param calendar_id: ID of the calendar of the events to be removed
        @return: Nothing
        """
        method_callable = lambda calendar, **kwargs: calendar.calendars.clear(**kwargs)
        method_args = {"calendarId": calendar_id}
        await execute_aiogoogle(method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args)

    async def add_share_rule(
        self, calendar_id: str, scope_type: str, user: str, role: str
    ) -> AclRuleModel:
        """
        Adds a share rule to the calendar
        @param calendar_id: ID of the calendar you want to add a rule to
        @param scope_type: Scope type, options: user, group and domain
        @param user: The user that it gets shared to
        @param role: The role of the user, options: reader, writer and owner
        @return: Returns the created rule
        """
        if role not in ["reader", "writer", "owner"]:
            raise Exception("Wrong role was give")
        if scope_type not in ["user", "group", "domain"]:
            raise Exception("Wrong scope type was given")

        rule = self._build_scope_body(scope_type, user, role)
        method_callable = lambda calendar, **kwargs: calendar.acl.insert(**kwargs)
        method_args = {"calendarId": calendar_id, "body": rule}
        return cast(
            AclRuleModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def get_share_rules(self, calendar_id: str) -> List[AclRuleModel]:
        """
        Returns all the share rules of the calendar
        @param calendar_id: ID of the calendar
        @return: Returns all the share rules
        """
        method_callable = lambda calendar, **kwargs: calendar.acl.list(**kwargs)
        method_args = {"calendarId": calendar_id}
        return cast(
            AclModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        ).get("items", [])

    async def get_share_rule(self, calendar_id: str, rule_id: str) -> AclRuleModel:
        """
        Returns the share rule of the calendar
        @param calendar_id: ID of the calendar
        @param rule_id: ID of the rule
        @return: The rule
        """
        method_callable = lambda calendar, **kwargs: calendar.acl.get(**kwargs)
        method_args = {"calendarId": calendar_id, "ruleId": rule_id}
        return cast(
            AclRuleModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def update_share_rule(
        self,
        calendar_id: str,
        rule_id: str,
        scope_type: str = None,
        user: str = None,
        role: str = None,
    ) -> AclRuleModel:
        """
        Updates the share rule of the calendar
        @param calendar_id: ID of the calendar you want to update the rule of
        @param rule_id: ID of the rule you want to update
        @param scope_type: Optional scope type, options: user, group and domain
        @param user: Optional user that it gets shared to
        @param role: Optional role of the user, options: reader, writer and owner
        @return: The updated rule
        """
        if all(x is None for x in [scope_type, user, role]):
            raise Exception("Not a single argument is updated")

        oldRule = await self.get_share_rule(calendar_id=calendar_id, rule_id=rule_id)

        currentScopeType = oldRule["scope"]["type"]
        currentUser = oldRule["scope"]["value"]
        currentRole = oldRule["role"]

        if scope_type is None:
            scope_type = currentScopeType
        elif scope_type not in ["user", "group", "domain"]:
            raise Exception("Wrong scope type was given")
        if user is None:
            user = currentUser
        if role is None:
            role = currentRole
        elif role not in ["reader", "writer", "owner"]:
            raise Exception("Wrong role was give")

        if scope_type == currentRole and user == currentUser and role == currentRole:
            raise Exception("Not a single parameter gets a new value")

        newRule = self._build_scope_body(scope_type, user, role)
        method_callable = lambda calendar, **kwargs: calendar.acl.update(**kwargs)
        method_args = {"calendarId": calendar_id, "ruleId": rule_id, "body": newRule}
        return cast(
            AclRuleModel,
            await execute_aiogoogle(
                method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args
            ),
        )

    async def remove_share_rule(self, calendar_id: str, rule_id: str) -> None:
        """
        Removes the share rule from the calendar
        @param calendar_id: ID of the calendar that the rule needs to be removed from
        @param rule_id: ID of the rule that needs to be removed
        @return: Nothing
        """
        method_callable = lambda calendar, **kwargs: calendar.acl.delete(**kwargs)
        method_args = {"calendarId": calendar_id, "ruleId": rule_id}
        await execute_aiogoogle(method_callable=method_callable, service_account_credentials=self.service_account_credentials, api_name=self.api_name, api_version=self.api_version, **method_args)
