"""
Calendly Integration — manage event types, scheduled events, and invitees via the Calendly API v2.

SETUP INSTRUCTIONS
==================

1. Log in to Calendly at https://calendly.com

2. Go to https://calendly.com/integrations/api_webhooks

3. Generate a Personal Access Token and copy it.

4. Add to your .env:
     CALENDLY_ACCESS_TOKEN=your-personal-access-token

IMPORTANT NOTES
===============
- Personal access tokens don't expire but can be revoked.
- The Calendly API uses URIs (not numeric IDs) to identify resources.
  Example: "https://api.calendly.com/event_types/abc123"
- Rate limit: 100 requests per minute.
- Pagination uses cursor-based pagination with "next_page_token".

Usage:
    from goliath.integrations.calendly import CalendlyClient

    cal = CalendlyClient()

    # Get current user
    user = cal.get_current_user()

    # List event types
    event_types = cal.list_event_types()

    # List scheduled events
    events = cal.list_scheduled_events()

    # Get invitees for an event
    invitees = cal.list_event_invitees(event_uri="https://api.calendly.com/scheduled_events/abc")
"""

import requests

from goliath import config

_API_BASE = "https://api.calendly.com"


class CalendlyClient:
    """Calendly API v2 client for scheduling and event management."""

    def __init__(self):
        if not config.CALENDLY_ACCESS_TOKEN:
            raise RuntimeError(
                "CALENDLY_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/calendly.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.CALENDLY_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )
        self._user_uri: str | None = None

    # -- User --------------------------------------------------------------

    def get_current_user(self) -> dict:
        """Get the authenticated user's info.

        Returns:
            User resource dict with uri, name, email, etc.
        """
        data = self._get("/users/me")
        user = data.get("resource", data)
        self._user_uri = user.get("uri")
        return user

    def _ensure_user_uri(self) -> str:
        """Resolve the current user's URI (cached after first call)."""
        if not self._user_uri:
            self.get_current_user()
        return self._user_uri  # type: ignore[return-value]

    # -- Event Types -------------------------------------------------------

    def list_event_types(
        self, active: bool | None = None, count: int = 20
    ) -> list[dict]:
        """List the user's event types.

        Args:
            active: Filter by active (True) or inactive (False). None = all.
            count:  Number of results (1–100).

        Returns:
            List of event type resource dicts.
        """
        user_uri = self._ensure_user_uri()
        params: dict = {"user": user_uri, "count": count}
        if active is not None:
            params["active"] = str(active).lower()
        return self._get("/event_types", params=params).get("collection", [])

    def get_event_type(self, event_type_uuid: str) -> dict:
        """Get an event type by UUID.

        Args:
            event_type_uuid: UUID portion of the event type URI.

        Returns:
            Event type resource dict.
        """
        return self._get(f"/event_types/{event_type_uuid}").get("resource", {})

    # -- Scheduled Events --------------------------------------------------

    def list_scheduled_events(
        self,
        status: str | None = None,
        min_start_time: str | None = None,
        max_start_time: str | None = None,
        count: int = 20,
    ) -> list[dict]:
        """List scheduled events.

        Args:
            status:         "active" or "canceled".
            min_start_time: ISO 8601 lower bound (e.g. "2025-06-01T00:00:00Z").
            max_start_time: ISO 8601 upper bound.
            count:          Number of results (1–100).

        Returns:
            List of scheduled event resource dicts.
        """
        user_uri = self._ensure_user_uri()
        params: dict = {"user": user_uri, "count": count}
        if status:
            params["status"] = status
        if min_start_time:
            params["min_start_time"] = min_start_time
        if max_start_time:
            params["max_start_time"] = max_start_time
        return self._get("/scheduled_events", params=params).get("collection", [])

    def get_scheduled_event(self, event_uuid: str) -> dict:
        """Get a scheduled event by UUID.

        Args:
            event_uuid: UUID portion of the event URI.

        Returns:
            Scheduled event resource dict.
        """
        return self._get(f"/scheduled_events/{event_uuid}").get("resource", {})

    def cancel_event(self, event_uuid: str, reason: str = "") -> dict:
        """Cancel a scheduled event.

        Args:
            event_uuid: UUID of the event.
            reason:     Cancellation reason.

        Returns:
            Cancellation response dict.
        """
        body: dict = {}
        if reason:
            body["reason"] = reason
        return self._post(f"/scheduled_events/{event_uuid}/cancellation", json=body)

    # -- Invitees ----------------------------------------------------------

    def list_event_invitees(self, event_uuid: str, count: int = 20) -> list[dict]:
        """List invitees for a scheduled event.

        Args:
            event_uuid: UUID portion of the event URI.
            count:      Number of results (1–100).

        Returns:
            List of invitee resource dicts.
        """
        return self._get(
            f"/scheduled_events/{event_uuid}/invitees", params={"count": count}
        ).get("collection", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
