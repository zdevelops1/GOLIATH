"""
Zoom Integration — create and manage meetings via the Zoom API v2.

SETUP INSTRUCTIONS
==================

1. Go to https://marketplace.zoom.us/ and sign in.

2. Click "Develop" > "Build App" > choose "Server-to-Server OAuth"
   (recommended for automation) or "OAuth" (for user-level access).

3. For Server-to-Server OAuth:
   - Note your Account ID, Client ID, and Client Secret.
   - Add required scopes: meeting:write:admin, meeting:read:admin,
     user:read:admin

4. For user-level OAuth:
   - Complete the OAuth 2.0 flow and set ZOOM_ACCESS_TOKEN.

5. Add to your .env:

   Option A — Server-to-Server OAuth (recommended):
     ZOOM_ACCOUNT_ID=your-account-id
     ZOOM_CLIENT_ID=your-client-id
     ZOOM_CLIENT_SECRET=your-client-secret

   Option B — User OAuth token:
     ZOOM_ACCESS_TOKEN=your-access-token

IMPORTANT NOTES
===============
- Server-to-Server tokens are auto-generated and last 1 hour.
- Meeting times use ISO 8601 format (e.g. "2025-06-01T09:00:00Z").
- Timezone defaults to UTC. Pass a timezone string (e.g. "America/New_York").
- Free accounts: max 40-minute group meetings.

Usage:
    from goliath.integrations.zoom import ZoomClient

    zoom = ZoomClient()

    # Create a meeting
    meeting = zoom.create_meeting(topic="Team Standup", start_time="2025-06-01T09:00:00Z", duration=30)

    # List upcoming meetings
    meetings = zoom.list_meetings()

    # Get meeting details
    details = zoom.get_meeting(meeting_id=123456789)

    # Delete a meeting
    zoom.delete_meeting(meeting_id=123456789)
"""

import requests

from goliath import config

_API_BASE = "https://api.zoom.us/v2"
_TOKEN_URL = "https://zoom.us/oauth/token"


class ZoomClient:
    """Zoom API v2 client for meeting management."""

    def __init__(self):
        has_s2s = (
            config.ZOOM_ACCOUNT_ID
            and config.ZOOM_CLIENT_ID
            and config.ZOOM_CLIENT_SECRET
        )
        has_token = bool(config.ZOOM_ACCESS_TOKEN)

        if not has_s2s and not has_token:
            raise RuntimeError(
                "Zoom credentials not set. Provide either "
                "ZOOM_ACCOUNT_ID + ZOOM_CLIENT_ID + ZOOM_CLIENT_SECRET "
                "(Server-to-Server OAuth) or ZOOM_ACCESS_TOKEN. "
                "See integrations/zoom.py for setup instructions."
            )

        self.session = requests.Session()

        if has_token:
            self.session.headers["Authorization"] = f"Bearer {config.ZOOM_ACCESS_TOKEN}"
        else:
            self._authenticate_s2s()

    def _authenticate_s2s(self):
        """Get an access token using Server-to-Server OAuth."""
        resp = requests.post(
            _TOKEN_URL,
            params={
                "grant_type": "account_credentials",
                "account_id": config.ZOOM_ACCOUNT_ID,
            },
            auth=(config.ZOOM_CLIENT_ID, config.ZOOM_CLIENT_SECRET),
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {token}"

    # -- Meetings ----------------------------------------------------------

    def list_meetings(
        self, user_id: str = "me", meeting_type: str = "upcoming", page_size: int = 30
    ) -> list[dict]:
        """List meetings for a user.

        Args:
            user_id:      Zoom user ID or "me" for authenticated user.
            meeting_type: "scheduled", "live", "upcoming", or "upcoming_meetings".
            page_size:    Number of results (1–300).

        Returns:
            List of meeting resource dicts.
        """
        return self._get(
            f"/users/{user_id}/meetings",
            params={"type": meeting_type, "page_size": page_size},
        ).get("meetings", [])

    def create_meeting(
        self,
        topic: str,
        start_time: str | None = None,
        duration: int = 60,
        timezone: str = "UTC",
        meeting_type: int = 2,
        user_id: str = "me",
        agenda: str = "",
        password: str | None = None,
    ) -> dict:
        """Create a meeting.

        Args:
            topic:        Meeting topic/title.
            start_time:   ISO 8601 start time (e.g. "2025-06-01T09:00:00Z").
            duration:     Duration in minutes.
            timezone:     Timezone string (e.g. "America/New_York").
            meeting_type: 1=instant, 2=scheduled, 3=recurring no fixed time,
                          8=recurring fixed time.
            user_id:      User to create meeting for ("me" or user ID).
            agenda:       Meeting agenda/description.
            password:     Optional meeting password.

        Returns:
            Created meeting resource dict with join_url.
        """
        body: dict = {
            "topic": topic,
            "type": meeting_type,
            "duration": duration,
            "timezone": timezone,
        }
        if start_time:
            body["start_time"] = start_time
        if agenda:
            body["agenda"] = agenda
        if password:
            body["password"] = password

        return self._post(f"/users/{user_id}/meetings", json=body)

    def get_meeting(self, meeting_id: int) -> dict:
        """Get meeting details.

        Args:
            meeting_id: Zoom meeting ID.

        Returns:
            Meeting resource dict.
        """
        return self._get(f"/meetings/{meeting_id}")

    def update_meeting(self, meeting_id: int, **kwargs) -> None:
        """Update a meeting.

        Args:
            meeting_id: Zoom meeting ID.
            kwargs:     Fields to update (topic, start_time, duration, etc.).
        """
        resp = self.session.patch(f"{_API_BASE}/meetings/{meeting_id}", json=kwargs)
        resp.raise_for_status()

    def delete_meeting(self, meeting_id: int) -> None:
        """Delete a meeting.

        Args:
            meeting_id: Zoom meeting ID.
        """
        resp = self.session.delete(f"{_API_BASE}/meetings/{meeting_id}")
        resp.raise_for_status()

    def get_meeting_participants(self, meeting_id: int) -> list[dict]:
        """Get participants of a past meeting.

        Args:
            meeting_id: Zoom meeting ID.

        Returns:
            List of participant dicts.
        """
        return self._get(f"/past_meetings/{meeting_id}/participants").get(
            "participants", []
        )

    # -- Users -------------------------------------------------------------

    def get_user(self, user_id: str = "me") -> dict:
        """Get user profile info.

        Args:
            user_id: Zoom user ID or "me".

        Returns:
            User resource dict.
        """
        return self._get(f"/users/{user_id}")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
