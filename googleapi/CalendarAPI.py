from os import path as os_path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError as GoogleHttpError
from datetime import datetime as datetime_datetime


class CalendarClass:
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
        self.service = self._build_service()

    def _build_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.serviceFilePath, scopes=self.scopes
        )
        credentials = credentials.with_subject(self.account)
        service = build("calendar", "v3", credentials=credentials)
        return service

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

    def add_event(
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
        eventBody = self._build_event_body(
            title, description, location, start_time, end_time
        )
        try:
            self.service.events().insert(
                calendarId=calendar_id, body=eventBody
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_events(self, calendar_id: str, get_all_events: bool = False) -> list[dict]:
        """
        :param get_all_events: Wether to return all events or only after the current date
        :param calendar_id: Id of the calendar
        :return: Returns all the events in the calendar
        """
        try:
            if get_all_events:
                events = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id, orderBy="startTime", singleEvents=True
                    )
                    .execute()
                    .get("items", [])
                )
            else:
                currentTime = datetime_datetime.utcnow()
                # Build the isoformat string, "Z" means that the date is in UTC timezone
                currentTime = currentTime.isoformat() + "Z"
                events = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        orderBy="startTime",
                        singleEvents=True,
                        timeMin=currentTime,
                    )
                    .execute()
                    .get("items", [])
                )
            return events
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_event(self, calendar_id: str, event_id: str) -> dict:
        """
        :param calendar_id: Id of the calendar
        :param event_id: Id of the event
        :return: Returns a dictionary of the event
        """
        try:
            event = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
            return event
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def remove_event(self, event_id: str, calendar_id: str) -> None:
        """
        :param calendar_id: Id of the calendar the event is in
        :param calendar_id: Id of the calendar the event is in
        :param event_id: Id of the event that needs to be removed
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_event(
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
        :param start_time: Start time of the event, optional
        :param end_time: End time of the event, optional
        :param description: Description of the event, optional
        :param location: Location of the event, optional
        :return: Nothing
        """
        if all(x is None for x in [title, start_time, end_time, description, location]):
            raise Exception("Update arguments don't have a value")

        try:
            oldEvent = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
        except GoogleHttpError as error:
            raise Exception(error.reason)

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

        try:
            self.service.events().update(
                calendarId=calendar_id, eventId=event_id, body=newEventBody
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def move_event(
        self, event_id: str, old_calendar_id: str, new_calendar_id: str
    ) -> None:
        """
        :param old_calendar_id: Id of the calendar is currently in
        :param event_id: Id of the event that needs to be moved
        :param new_calendar_id: Id of the calendar the event is moved to
        :return: Nothing
        """
        try:
            self.service.events().move(
                calendarId=old_calendar_id,
                eventId=event_id,
                destination=new_calendar_id,
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def add_calendar(
        self, title: str, location: str = "", description: str = ""
    ) -> None:
        """
        :param title: Title of the calendar
        :param location: Geographical location of the calendar, optional
        :param description: Description of the calendar, optional
        :return: Nothing
        """
        try:
            calendarBody = self._build_calendar_body(title, location, description)
            self.service.calendars().insert(body=calendarBody).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_calendars(self) -> list[dict]:
        """
        :return: Returns all the calendars
        """
        try:
            calendars = self.service.calendarList().list().execute().get("items", [])
            return calendars
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_calendar(self, calendar_id: str) -> dict:
        """
        :param calendar_id: Id of the calendar
        :return: Returns the calendar
        """
        try:
            calendar = self.service.calendars().get(calendarId=calendar_id).execute()
            return calendar
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_calendar(
        self,
        calendar_id: str,
        title: str = None,
        location: str = None,
        description: str = None,
    ):
        """
        :param calendar_id: Id of the calendar that needs to be updated
        :param title: Title of the calendar
        :param location: Geographical location of the calendar, optional
        :param description: Description of the calendar, optional
        :return: Nothing
        """
        if all(x is None for x in [title, description, location]):
            raise Exception("Not a single argument is updated")
        try:
            oldCalendar = self.service.calendars().get(calendarId=calendar_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

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

        try:
            self.service.calendars().update(
                calendarId=calendar_id, body=newCalendarBody
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def remove_calendar(self, calendar_id: str):
        """
        Removes the calendar itself
        """
        try:
            self.service.calendars().delete(calendarId=calendar_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def clear_calendar(self, calendar_id: str):
        """
        Removes all the events in the calendar
        """
        try:
            self.service.calendars().clear(calendarId=calendar_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def add_share_rule(
        self, calendar_id: str, scope_type: str, user: str, role: str
    ) -> None:
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
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_share_rules(self, calendar_id: str) -> list[dict]:
        """
        :param calendar_id: Id of the calendar
        :return: Returns all the share rules
        """
        try:
            shareRules = (
                self.service.acl()
                .list(calendarId=calendar_id)
                .execute()
                .get("items", [])
            )
            return shareRules
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def get_share_rule(self, calendar_id: str, rule_id: str) -> dict:
        """
        :param calendar_id: Id of the calendar
        :param rule_id: Id of the rule
        :return: Dictionary of the rule
        """
        try:
            shareRule = (
                self.service.acl().get(calendarId=calendar_id, ruleId=rule_id).execute()
            )
            return shareRule
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def update_share_rule(
        self,
        calendar_id: str,
        rule_id: str,
        scope_type: str = None,
        user: str = None,
        role: str = None,
    ) -> None:
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

        try:
            oldRule = (
                self.service.acl().get(calendarId=calendar_id, ruleId=rule_id).execute()
            )
        except GoogleHttpError as error:
            raise Exception(error.reason)

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
            self.service.acl().update(
                calendarId=calendar_id, ruleId=rule_id, body=newRule
            ).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)

    def remove_share_rule(self, calendar_id: str, rule_id: str) -> None:
        """
        :param calendar_id: Id of the calendar that the rule needs to be removed from
        :param rule_id: Id of the rule that needs to be removed
        :return: Nothing
        """
        try:
            self.service.acl().delete(calendarId=calendar_id, ruleId=rule_id).execute()
        except GoogleHttpError as error:
            raise Exception(error.reason)