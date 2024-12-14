import json
from typing import cast, List

import aiogoogle.excs
from os import path as os_path
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from datetime import datetime as datetime_datetime, timezone

from googleapi.TypedDicts.Calendar import CalendarListModel, CalendarListEntryModel, CalendarModel, EventsModel, \
    EventModel, AclRuleModel, AclModel


class Calendar:
    """
    Implements the Google Calendar API to add events to our calendars
    """

    def __init__(self, service_file_path: str, account: str) -> None:
        """
        :param service_file_path: Path to the service file
        """
        self.scopes = ["https://www.googleapis.com/auth/calendar"]
        self.timeZone = "Europe/Brussels"
        self.account = account

        if not os_path.exists(service_file_path):
            raise Exception("Service account json path does not exist")

        self.serviceFilePath = service_file_path
        self.service_account_credentials = self._build_service_account_credentials()

    def _build_service_account_credentials(self):
        service_account_key = json.load(open(self.serviceFilePath))
        credentials = ServiceAccountCreds(scopes=self.scopes, **service_account_key)
        return credentials

    def _build_event_body(
            self,
            title: str,
            description: str,
            location: str,
            start_time: datetime_datetime,
            end_time: datetime_datetime,
    ) -> dict:
        eventBody = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": self.timeZone},
            "end": {"dateTime": end_time.isoformat(), "timeZone": self.timeZone},
        }
        return eventBody

    def _build_calendar_body(self, title: str, location: str, description: str) -> dict:
        calendarBody = {
            "summary": title,
            "location": location,
            "description": description,
            "timeZone": self.timeZone,
        }
        return calendarBody

    def _build_scope_body(self, scope_type: str, scope_value: str, role: str) -> dict:
        rule = {"scope": {"type": scope_type, "value": scope_value}, "role": role}
        return rule

    async def add_event(
            self,
            calendar_id: str,
            title: str,
            start_time: datetime_datetime,
            end_time: datetime_datetime,
            description: str = "",
            location: str = "",
    ) -> None:
        """
        :param calendar_id: Id of the calendar that the event needs to be added to
        :param title: Title of the event
        :param start_time: Start time of the event
        :param end_time: End time of the event
        :param description: Description of the event, optional
        :param location: Location of the event, optional
        :return: Nothing
        """
        eventBody = self._build_event_body(title, description, location, start_time, end_time)

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.events.insert(calendarId=calendar_id, body=eventBody))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_events(self, calendar_id: str, get_all_events: bool = False) -> List[EventsModel]:
        """
        :param get_all_events: Whether to return all events or only after the current date
        :param calendar_id: Id of the calendar
        :return: Returns all the events in the calendar
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                if get_all_events:
                    return cast(EventsModel, await google.as_service_account(calendar.events.list(calendarId=calendar_id, orderBy="startTime", singleEvents=True))).get("items", [])
                else:
                    currentTime = datetime_datetime.now(timezone.utc).isoformat()
                    return cast(EventsModel, await google.as_service_account(calendar.events.list(calendarId=calendar_id, orderBy="startTime", singleEvents=True, timeMin=currentTime))).get("items", [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_event(self, calendar_id: str, event_id: str) -> EventModel:
        """
        :param calendar_id: Id of the calendar
        :param event_id: Id of the event
        :return: Returns a dictionary of the event
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                return cast(EventModel, await google.as_service_account(calendar.events.get(calendarId=calendar_id, eventId=event_id)))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def remove_event(self, event_id: str, calendar_id: str) -> None:
        """
        :param calendar_id: Id of the calendar the event is in
        :param calendar_id: Id of the calendar the event is in
        :param event_id: Id of the event that needs to be removed
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.events.delete(calendarId=calendar_id, eventId=event_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_event(
            self,
            event_id: str,
            calendar_id: str,
            title: str = None,
            start_time: datetime_datetime = None,
            end_time: datetime_datetime = None,
            description: str = None,
            location: str = None,
    ) -> None:
        """
        :param calendar_id: If of the calendar the event is in
        :param event_id: Id of the event that needs to be updated
        :param title: Title of the event, optional
        :param start_time: Start time of the event in isoformat, optional
        :param end_time: End time of the event in isoformat, optional
        :param description: Description of the event, optional
        :param location: Location of the event, optional
        :return: Nothing
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
                title == currentTitle and start_time == currentStartTime and end_time == currentEndTime and description == currentDescription and location == currentLocation):
            raise Exception("Not a single parameter gets a new value")

        newEventBody = self._build_event_body(title, description, location, start_time, end_time)

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(
                    calendar.events.update(calendarId=calendar_id, eventId=event_id, body=newEventBody))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def move_event(self, event_id: str, old_calendar_id: str, new_calendar_id: str) -> None:
        """
        :param old_calendar_id: Id of the calendar is currently in
        :param event_id: Id of the event that needs to be moved
        :param new_calendar_id: Id of the calendar the event is moved to
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(
                    calendar.events.move(calendarId=old_calendar_id, eventId=event_id, destination=new_calendar_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def add_calendar(self, title: str, location: str = "", description: str = "") -> None:
        """
        :param title: Title of the calendar
        :param location: Geographical location of the calendar, optional
        :param description: Description of the calendar, optional
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                calendarBody = self._build_calendar_body(title, location, description)
                await google.as_service_account(calendar.calendars.insert(body=calendarBody))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_calendars(self) -> List[CalendarListEntryModel]:
        """
        :return: Returns all the calendars
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                return cast(CalendarListModel, await google.as_service_account(calendar.calendarList.list())).get("items", [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_calendar(self, calendar_id: str) -> CalendarModel:
        """
        :param calendar_id: Id of the calendar
        :return: Returns the calendar
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                return cast(CalendarModel, await google.as_service_account(calendar.calendars.insert(id=calendar_id)))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_calendar(self, calendar_id: str, title: str = None, location: str = None, description: str = None):
        """
        :param calendar_id: Id of the calendar that needs to be updated
        :param title: Title of the calendar
        :param location: Geographical location of the calendar, optional
        :param description: Description of the calendar, optional
        :return: Nothing
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

        if title == currentTitle and description == currentDescription and location == currentLocation:
            raise Exception("Not a single parameter gets a new value")

        newCalendarBody = self._build_calendar_body(title, location, description)

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.calendars.update(calendarId=calendar_id, body=newCalendarBody))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def remove_calendar(self, calendar_id: str):
        """
        Removes the calendar itself
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.calendars.delete(calendarId=calendar_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def clear_calendar(self, calendar_id: str):
        """
        Removes all the events in the calendar
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.calendars.clear(calendarId=calendar_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def add_share_rule(self, calendar_id: str, scope_type: str, user: str, role: str) -> None:
        """
        :param calendar_id: Id of the calendar you want to add a rule to
        :param scope_type: Scope type, options: user, group and domain
        :param user: The user that it gets shared to
        :param role: The role of the user, options: reader, writer and owner
        :return: Returns the id of the rule
        """
        if role not in ["reader", "writer", "owner"]:
            raise Exception("Wrong role was give")
        if scope_type not in ["user", "group", "domain"]:
            raise Exception("Wrong scope type was given")

        rule = self._build_scope_body(scope_type, user, role)

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.acl.insert(calendarId=calendar_id, body=rule))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_share_rules(self, calendar_id: str) -> List[AclRuleModel]:
        """
        :param calendar_id: Id of the calendar
        :return: Returns all the share rules
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                return cast(AclModel, await google.as_service_account(calendar.acl.list(calendarId=calendar_id))).get("items", [])
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def get_share_rule(self, calendar_id: str, rule_id: str) -> AclRuleModel:
        """
        :param calendar_id: Id of the calendar
        :param rule_id: Id of the rule
        :return: Dictionary of the rule
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                return cast(AclRuleModel, await google.as_service_account(calendar.acl.get(calendarId=calendar_id, ruleId=rule_id)))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def update_share_rule(self, calendar_id: str, rule_id: str, scope_type: str = None, user: str = None,
                                role: str = None, ) -> None:
        """
        :param calendar_id: Id of the calendar you want to update the rule of
        :param rule_id: Id of the rule you want to update
        :param scope_type: Scope type, options: user, group and domain, optional
        :param user: The user that it gets shared to, optional
        :param role: The role of the user, options: reader, writer and owner, optional
        :return: Nothing
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

        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(
                    calendar.acl.update(calendarId=calendar_id, ruleId=rule_id, body=newRule))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error

    async def remove_share_rule(self, calendar_id: str, rule_id: str) -> None:
        """
        :param calendar_id: Id of the calendar that the rule needs to be removed from
        :param rule_id: Id of the rule that needs to be removed
        :return: Nothing
        """
        try:
            async with Aiogoogle(service_account_creds=self.service_account_credentials) as google:
                calendar = await google.discover("calendar", "v3")
                await google.as_service_account(calendar.acl.delete(calendarId=calendar_id, ruleId=rule_id))
        except aiogoogle.excs.HTTPError as error:
            raise Exception("Aiogoogle error") from error
