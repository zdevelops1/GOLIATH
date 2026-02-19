"""
Google Calendar Integration — list, create, update, and delete events.

SETUP INSTRUCTIONS
==================

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create a service account (or reuse the one from Sheets/Drive/Docs).
3. Download its JSON key file.
4. Enable the Google Calendar API for your project:
     https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
5. Share the target calendar with the service account email
   (name@project-id.iam.gserviceaccount.com) — give it "Make changes to events"
   permission for full read/write access.
6. Add the path to your .env:
     GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

Usage:
    from goliath.integrations.calendar import CalendarClient

    cal = CalendarClient()

    # List upcoming events
    events = cal.list_events()

    # Create an event
    cal.create_event(
        summary="Team standup",
        start="2025-06-01T09:00:00",
        end="2025-06-01T09:30:00",
        timezone="America/New_York",
        description="Daily sync meeting",
    )

    # Update an event
    cal.update_event("EVENT_ID", summary="Updated standup", location="Room 42")

    # Delete an event
    cal.delete_event("EVENT_ID")
"""

import requests

from goliath import config

_BASE_URL = "https://www.googleapis.com/calendar/v3"


class CalendarClient:
    """Google Calendar API v3 client for managing calendar events."""

    def __init__(self, calendar_id: str = "primary"):
        """Initialize the Calendar client.

        Args:
            calendar_id: Calendar to operate on. Defaults to "primary".
                         For shared calendars, use the calendar's email address.
        """
        if not config.GOOGLE_SERVICE_ACCOUNT_FILE:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_FILE is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/calendar.py for setup instructions."
            )

        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        scopes = ["https://www.googleapis.com/auth/calendar"]
        self._credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes,
        )
        self.calendar_id = calendar_id
        self.session = requests.Session()
        self._refresh_token()

    def _refresh_token(self):
        """Refresh the access token if expired."""
        from google.auth.transport.requests import Request

        if not self._credentials.valid or self._credentials.expired:
            self._credentials.refresh(Request())
            self.session.headers["Authorization"] = f"Bearer {self._credentials.token}"

    # -- public API --------------------------------------------------------

    def list_events(
        self,
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 50,
        query: str | None = None,
    ) -> list[dict]:
        """List events from the calendar.

        Args:
            time_min:    Lower bound (RFC3339, e.g. "2025-06-01T00:00:00Z").
                         Defaults to now.
            time_max:    Upper bound (RFC3339).
            max_results: Maximum number of events to return.
            query:       Free-text search term.

        Returns:
            List of event resource dicts.
        """
        params: dict = {
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if query:
            params["q"] = query

        data = self._get(f"/calendars/{self.calendar_id}/events", params=params)
        return data.get("items", [])

    def get_event(self, event_id: str) -> dict:
        """Get a single event by ID.

        Args:
            event_id: The event ID.

        Returns:
            Event resource dict.
        """
        return self._get(f"/calendars/{self.calendar_id}/events/{event_id}")

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        timezone: str = "UTC",
        description: str = "",
        location: str = "",
        attendees: list[str] | None = None,
    ) -> dict:
        """Create a new calendar event.

        Args:
            summary:     Event title.
            start:       Start datetime (ISO 8601, e.g. "2025-06-01T09:00:00").
            end:         End datetime.
            timezone:    IANA timezone name.
            description: Optional event description.
            location:    Optional event location.
            attendees:   Optional list of attendee email addresses.

        Returns:
            Created event resource dict.
        """
        body: dict = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]

        return self._post(f"/calendars/{self.calendar_id}/events", json=body)

    def update_event(self, event_id: str, **fields) -> dict:
        """Update an existing event.

        Pass any event fields as keyword arguments:
            summary, description, location, start, end, etc.

        For start/end, pass a dict like {"dateTime": "...", "timeZone": "..."}.

        Args:
            event_id: The event ID to update.
            **fields: Fields to update on the event resource.

        Returns:
            Updated event resource dict.
        """
        return self._patch(
            f"/calendars/{self.calendar_id}/events/{event_id}",
            json=fields,
        )

    def delete_event(self, event_id: str) -> None:
        """Delete an event.

        Args:
            event_id: The event ID to delete.
        """
        self._delete(f"/calendars/{self.calendar_id}/events/{event_id}")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.get(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.post(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.patch(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, **kwargs) -> None:
        self._refresh_token()
        resp = self.session.delete(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
