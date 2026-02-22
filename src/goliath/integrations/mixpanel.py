"""
Mixpanel Integration — track events and query analytics via the Mixpanel API.

SETUP INSTRUCTIONS
==================

1. Log in to Mixpanel at https://mixpanel.com/

2. Go to Settings > Project Settings to find your Project Token
   (used for tracking / ingestion).

3. For data export / query APIs, create a Service Account:
   Go to Settings > Service Accounts, click "Add Service Account".
   Copy the username and secret.

4. Add to your .env:
     MIXPANEL_PROJECT_TOKEN=your-project-token
     MIXPANEL_SERVICE_ACCOUNT_USER=your-service-account-username
     MIXPANEL_SERVICE_ACCOUNT_SECRET=your-service-account-secret

5. Optionally set your project ID (required for query APIs):
     MIXPANEL_PROJECT_ID=12345

IMPORTANT NOTES
===============
- Ingestion API: https://api.mixpanel.com/track
- Query / Export API: https://data.mixpanel.com/api/2.0/ or https://mixpanel.com/api/
- API docs: https://developer.mixpanel.com/reference
- Rate limit: varies by plan.

Usage:
    from goliath.integrations.mixpanel import MixpanelClient

    mp = MixpanelClient()

    # Track an event
    mp.track(distinct_id="user-123", event="Purchase", properties={"amount": 49.99})

    # Track multiple events
    mp.track_batch([
        {"event": "Page View", "properties": {"distinct_id": "user-123", "page": "/home"}},
        {"event": "Click", "properties": {"distinct_id": "user-123", "button": "CTA"}},
    ])

    # Query top events (requires service account)
    top = mp.top_events(event_type="general", limit=10)

    # Export raw events
    data = mp.export_events(from_date="2025-01-01", to_date="2025-01-31")

    # User profile: set properties
    mp.set_user("user-123", {"$name": "Alice", "plan": "pro"})
"""

import base64
import json

import requests

from goliath import config

_TRACK_URL = "https://api.mixpanel.com"
_QUERY_BASE = "https://mixpanel.com/api/2.0"
_EXPORT_BASE = "https://data.mixpanel.com/api/2.0"


class MixpanelClient:
    """Mixpanel API client for event tracking and analytics queries."""

    def __init__(self):
        if not config.MIXPANEL_PROJECT_TOKEN:
            raise RuntimeError(
                "MIXPANEL_PROJECT_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/mixpanel.py for setup instructions."
            )

        self.token = config.MIXPANEL_PROJECT_TOKEN
        self.project_id = getattr(config, "MIXPANEL_PROJECT_ID", "") or ""
        self._sa_user = (
            getattr(config, "MIXPANEL_SERVICE_ACCOUNT_USER", "") or ""
        )
        self._sa_secret = (
            getattr(config, "MIXPANEL_SERVICE_ACCOUNT_SECRET", "") or ""
        )

        self.session = requests.Session()

    # -- Event Tracking --------------------------------------------------------

    def track(
        self,
        distinct_id: str,
        event: str,
        properties: dict | None = None,
    ) -> dict:
        """Track a single event.

        Args:
            distinct_id: Unique user identifier.
            event:       Event name.
            properties:  Event properties dict.

        Returns:
            Tracking result.
        """
        props = dict(properties or {})
        props["distinct_id"] = distinct_id
        props["token"] = self.token

        payload = [{"event": event, "properties": props}]
        resp = self.session.post(
            f"{_TRACK_URL}/track",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def track_batch(self, events: list[dict]) -> dict:
        """Track multiple events.

        Args:
            events: List of event dicts, each with "event" and "properties" keys.
                    "properties" must include "distinct_id".

        Returns:
            Tracking result.
        """
        for ev in events:
            ev.setdefault("properties", {})["token"] = self.token

        resp = self.session.post(
            f"{_TRACK_URL}/track",
            json=events,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    # -- User Profiles ---------------------------------------------------------

    def set_user(self, distinct_id: str, properties: dict) -> dict:
        """Set user profile properties.

        Args:
            distinct_id: User identifier.
            properties:  Properties to set (e.g. {"$name": "Alice"}).

        Returns:
            API result.
        """
        payload = [{
            "$token": self.token,
            "$distinct_id": distinct_id,
            "$set": properties,
        }]
        resp = self.session.post(
            f"{_TRACK_URL}/engage",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    # -- Query APIs (require service account) ----------------------------------

    def top_events(
        self,
        event_type: str = "general",
        limit: int = 10,
    ) -> dict:
        """Get top events.

        Args:
            event_type: "general" or "average".
            limit:      Number of events to return.

        Returns:
            Top events dict.
        """
        params: dict = {"type": event_type, "limit": limit}
        return self._query_get("/events/top", params=params)

    def export_events(
        self,
        from_date: str,
        to_date: str,
        event: str | None = None,
    ) -> list[dict]:
        """Export raw event data.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date:   End date (YYYY-MM-DD).
            event:     Filter by event name.

        Returns:
            List of event dicts.
        """
        params: dict = {"from_date": from_date, "to_date": to_date}
        if event:
            params["event"] = json.dumps([event])

        resp = self.session.get(
            f"{_EXPORT_BASE}/export",
            params=params,
            headers=self._sa_auth_headers(),
        )
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        return [json.loads(line) for line in lines if line]

    # -- internal helpers ------------------------------------------------------

    def _sa_auth_headers(self) -> dict:
        """Build Basic auth headers from service account credentials."""
        if not self._sa_user or not self._sa_secret:
            raise RuntimeError(
                "Service account credentials required for query APIs. "
                "Set MIXPANEL_SERVICE_ACCOUNT_USER and "
                "MIXPANEL_SERVICE_ACCOUNT_SECRET."
            )
        creds = base64.b64encode(
            f"{self._sa_user}:{self._sa_secret}".encode()
        ).decode()
        return {"Authorization": f"Basic {creds}"}

    def _query_get(self, path: str, **kwargs) -> dict:
        """GET against the query API with service account auth."""
        headers = kwargs.pop("headers", {})
        headers.update(self._sa_auth_headers())
        if self.project_id:
            headers["X-Mixpanel-Project-Id"] = self.project_id
        resp = self.session.get(
            f"{_QUERY_BASE}{path}", headers=headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()
