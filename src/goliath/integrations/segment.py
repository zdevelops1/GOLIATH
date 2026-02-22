"""
Segment Integration — send events, identify users, and manage sources via the Segment API.

SETUP INSTRUCTIONS
==================

1. Log in to Segment at https://app.segment.com/

2. Go to Connections > Sources and select (or create) a source.

3. Find the Write Key on the source's Settings > API Keys page.

4. Add the write key to your .env:
     SEGMENT_WRITE_KEY=your-write-key

5. For the Config API (managing sources/destinations), create a Public API token:
   Settings > Workspace Settings > Access Management > Tokens
     SEGMENT_API_TOKEN=your-api-token

IMPORTANT NOTES
===============
- Tracking API docs: https://segment.com/docs/connections/sources/catalog/libraries/server/http-api/
- Config API docs: https://docs.segmentapis.com/
- Tracking endpoint: https://api.segment.io/v1/
- Authentication: Basic auth with write key as username, empty password.

Usage:
    from goliath.integrations.segment import SegmentClient

    seg = SegmentClient()

    # Identify a user
    seg.identify(user_id="user-123", traits={"name": "Alice", "plan": "pro"})

    # Track an event
    seg.track(user_id="user-123", event="Purchase", properties={"amount": 49.99})

    # Page view
    seg.page(user_id="user-123", name="Home", properties={"url": "/home"})

    # Group
    seg.group(user_id="user-123", group_id="company-456", traits={"name": "Acme"})

    # Batch send
    seg.batch([
        {"type": "identify", "userId": "u1", "traits": {"name": "Bob"}},
        {"type": "track", "userId": "u1", "event": "Login"},
    ])
"""

import base64

import requests

from goliath import config

_TRACKING_BASE = "https://api.segment.io/v1"


class SegmentClient:
    """Segment HTTP API client for event tracking and user identification."""

    def __init__(self):
        if not config.SEGMENT_WRITE_KEY:
            raise RuntimeError(
                "SEGMENT_WRITE_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/segment.py for setup instructions."
            )

        self.write_key = config.SEGMENT_WRITE_KEY

        # Segment uses Basic auth: write_key as username, empty password.
        creds = base64.b64encode(f"{self.write_key}:".encode()).decode()

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
        })

    # -- Core API methods ------------------------------------------------------

    def identify(
        self,
        user_id: str,
        traits: dict | None = None,
        anonymous_id: str | None = None,
        context: dict | None = None,
    ) -> dict:
        """Identify a user with traits.

        Args:
            user_id:      User ID.
            traits:       User traits dict.
            anonymous_id: Anonymous ID (if user_id not yet known).
            context:      Context dict (ip, userAgent, etc.).

        Returns:
            API result.
        """
        payload: dict = {"userId": user_id, "traits": traits or {}}
        if anonymous_id:
            payload["anonymousId"] = anonymous_id
        if context:
            payload["context"] = context
        return self._post("/identify", json=payload)

    def track(
        self,
        user_id: str,
        event: str,
        properties: dict | None = None,
        anonymous_id: str | None = None,
        context: dict | None = None,
    ) -> dict:
        """Track an event.

        Args:
            user_id:      User ID.
            event:        Event name.
            properties:   Event properties.
            anonymous_id: Anonymous ID.
            context:      Context dict.

        Returns:
            API result.
        """
        payload: dict = {
            "userId": user_id,
            "event": event,
            "properties": properties or {},
        }
        if anonymous_id:
            payload["anonymousId"] = anonymous_id
        if context:
            payload["context"] = context
        return self._post("/track", json=payload)

    def page(
        self,
        user_id: str,
        name: str = "",
        properties: dict | None = None,
        category: str | None = None,
    ) -> dict:
        """Record a page view.

        Args:
            user_id:    User ID.
            name:       Page name.
            properties: Page properties (url, referrer, etc.).
            category:   Page category.

        Returns:
            API result.
        """
        payload: dict = {
            "userId": user_id,
            "name": name,
            "properties": properties or {},
        }
        if category:
            payload["category"] = category
        return self._post("/page", json=payload)

    def group(
        self,
        user_id: str,
        group_id: str,
        traits: dict | None = None,
    ) -> dict:
        """Associate a user with a group (company, team, etc.).

        Args:
            user_id:  User ID.
            group_id: Group ID.
            traits:   Group traits.

        Returns:
            API result.
        """
        payload: dict = {
            "userId": user_id,
            "groupId": group_id,
            "traits": traits or {},
        }
        return self._post("/group", json=payload)

    def alias(self, previous_id: str, user_id: str) -> dict:
        """Merge two user identities.

        Args:
            previous_id: Previous (anonymous) user ID.
            user_id:     New canonical user ID.

        Returns:
            API result.
        """
        return self._post(
            "/alias", json={"previousId": previous_id, "userId": user_id}
        )

    def batch(self, messages: list[dict]) -> dict:
        """Send a batch of messages (identify, track, page, group, alias).

        Args:
            messages: List of message dicts, each must have a "type" field.

        Returns:
            API result.
        """
        return self._post("/batch", json={"batch": messages})

    # -- internal helpers ------------------------------------------------------

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_TRACKING_BASE}{path}", **kwargs)
        resp.raise_for_status()
        # Segment returns {"success": true} on 200
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"success": True}
        return {"success": True}
