"""
Twitch Integration — manage channels, streams, and chat via the Twitch Helix API.

SETUP INSTRUCTIONS
==================

1. Go to https://dev.twitch.tv/console and log in with your Twitch account.

2. Click "Register Your Application".

3. Fill in:
   - Name: "GOLIATH" (or any name)
   - OAuth Redirect URLs: http://localhost
   - Category: Application Integration

4. Copy the Client ID and generate a Client Secret.

5. Add to your .env:
     TWITCH_CLIENT_ID=abc123def456
     TWITCH_CLIENT_SECRET=xyz789secret
     TWITCH_ACCESS_TOKEN=oauth_token_here  (optional — auto-generated if empty)

   To get a user access token (for chat, channel management), use the OAuth
   Authorization Code flow. For app-level access (search, public data), the
   client credentials flow is used automatically.

IMPORTANT NOTES
===============
- Helix API docs: https://dev.twitch.tv/docs/api/reference/
- Rate limit: 800 points per minute.
- Some endpoints require a user access token; others work with app tokens.
- If TWITCH_ACCESS_TOKEN is not set, the client auto-generates an app token.

Usage:
    from goliath.integrations.twitch import TwitchClient

    tw = TwitchClient()

    # Search channels
    channels = tw.search_channels("speedrunning")

    # Get stream info
    streams = tw.get_streams(user_login=["shroud", "pokimane"])

    # Get user info
    users = tw.get_users(logins=["ninja"])

    # Get top games
    games = tw.get_top_games(limit=10)

    # Get channel info
    info = tw.get_channel("12345678")

    # Send chat message (requires user access token with chat scopes)
    tw.send_chat_message(broadcaster_id="12345678", message="Hello chat!")
"""

import requests

from goliath import config

_API_BASE = "https://api.twitch.tv/helix"
_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


class TwitchClient:
    """Twitch Helix API client for channels, streams, and chat."""

    def __init__(self):
        if not config.TWITCH_CLIENT_ID:
            raise RuntimeError(
                "TWITCH_CLIENT_ID is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/twitch.py for setup instructions."
            )

        self.client_id = config.TWITCH_CLIENT_ID
        self.client_secret = config.TWITCH_CLIENT_SECRET
        self.access_token = config.TWITCH_ACCESS_TOKEN

        # Auto-generate app access token if none provided
        if not self.access_token:
            if not self.client_secret:
                raise RuntimeError(
                    "TWITCH_CLIENT_SECRET is required when TWITCH_ACCESS_TOKEN "
                    "is not set (for auto-generating an app token)."
                )
            self.access_token = self._get_app_token()

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Client-Id": self.client_id,
        })

    # -- Users -------------------------------------------------------------

    def get_users(
        self,
        ids: list[str] | None = None,
        logins: list[str] | None = None,
    ) -> list[dict]:
        """Get user info by ID or login name.

        Args:
            ids:    List of user IDs (max 100).
            logins: List of login names (max 100).

        Returns:
            List of user dicts.
        """
        params: list[tuple[str, str]] = []
        if ids:
            params.extend(("id", uid) for uid in ids)
        if logins:
            params.extend(("login", login) for login in logins)
        return self._get("/users", params=params)

    # -- Streams -----------------------------------------------------------

    def get_streams(
        self,
        user_id: list[str] | None = None,
        user_login: list[str] | None = None,
        game_id: list[str] | None = None,
        first: int = 20,
    ) -> list[dict]:
        """Get active streams.

        Args:
            user_id:    Filter by user IDs.
            user_login: Filter by login names.
            game_id:    Filter by game IDs.
            first:      Max results (1–100).

        Returns:
            List of stream dicts.
        """
        params: list[tuple[str, str]] = [("first", str(first))]
        if user_id:
            params.extend(("user_id", uid) for uid in user_id)
        if user_login:
            params.extend(("user_login", login) for login in user_login)
        if game_id:
            params.extend(("game_id", gid) for gid in game_id)
        return self._get("/streams", params=params)

    # -- Channels ----------------------------------------------------------

    def get_channel(self, broadcaster_id: str) -> dict:
        """Get channel info.

        Args:
            broadcaster_id: Broadcaster user ID.

        Returns:
            Channel dict.
        """
        data = self._get("/channels", params={"broadcaster_id": broadcaster_id})
        return data[0] if data else {}

    def search_channels(self, query: str, first: int = 20, live_only: bool = False) -> list[dict]:
        """Search channels by name.

        Args:
            query:     Search query.
            first:     Max results (1–100).
            live_only: Only return channels that are currently live.

        Returns:
            List of channel dicts.
        """
        params = {"query": query, "first": first, "live_only": str(live_only).lower()}
        return self._get("/search/channels", params=params)

    def modify_channel(
        self,
        broadcaster_id: str,
        title: str | None = None,
        game_id: str | None = None,
        broadcaster_language: str | None = None,
    ) -> None:
        """Modify channel information.

        Args:
            broadcaster_id:       Broadcaster user ID.
            title:                Stream title.
            game_id:              Game/category ID.
            broadcaster_language: Language (ISO 639-1 code).
        """
        data: dict = {}
        if title is not None:
            data["title"] = title
        if game_id is not None:
            data["game_id"] = game_id
        if broadcaster_language is not None:
            data["broadcaster_language"] = broadcaster_language

        resp = self.session.patch(
            f"{_API_BASE}/channels",
            params={"broadcaster_id": broadcaster_id},
            json=data,
        )
        resp.raise_for_status()

    # -- Games / Categories ------------------------------------------------

    def get_top_games(self, limit: int = 20) -> list[dict]:
        """Get top games/categories by viewership.

        Args:
            limit: Max results (1–100).

        Returns:
            List of game dicts.
        """
        return self._get("/games/top", params={"first": limit})

    def get_games(self, ids: list[str] | None = None, names: list[str] | None = None) -> list[dict]:
        """Get games by ID or name.

        Args:
            ids:   List of game IDs.
            names: List of game names.

        Returns:
            List of game dicts.
        """
        params: list[tuple[str, str]] = []
        if ids:
            params.extend(("id", gid) for gid in ids)
        if names:
            params.extend(("name", name) for name in names)
        return self._get("/games", params=params)

    # -- Chat --------------------------------------------------------------

    def send_chat_message(
        self,
        broadcaster_id: str,
        message: str,
        sender_id: str | None = None,
    ) -> dict:
        """Send a chat message to a channel.

        Requires a user access token with user:write:chat scope.

        Args:
            broadcaster_id: Channel broadcaster ID.
            message:        Message text.
            sender_id:      Sender user ID (defaults to the token owner).

        Returns:
            Response dict.
        """
        data: dict = {"broadcaster_id": broadcaster_id, "message": message}
        if sender_id:
            data["sender_id"] = sender_id
        resp = self.session.post(f"{_API_BASE}/chat/messages", json=data)
        resp.raise_for_status()
        return resp.json().get("data", [{}])[0] if resp.content else {"status": "sent"}

    # -- Clips -------------------------------------------------------------

    def get_clips(
        self,
        broadcaster_id: str | None = None,
        game_id: str | None = None,
        first: int = 20,
    ) -> list[dict]:
        """Get clips for a broadcaster or game.

        Args:
            broadcaster_id: Broadcaster user ID.
            game_id:        Game ID.
            first:          Max results (1–100).

        Returns:
            List of clip dicts.
        """
        params: dict = {"first": first}
        if broadcaster_id:
            params["broadcaster_id"] = broadcaster_id
        if game_id:
            params["game_id"] = game_id
        return self._get("/clips", params=params)

    # -- internal helpers --------------------------------------------------

    def _get_app_token(self) -> str:
        """Generate an app access token using client credentials."""
        resp = requests.post(
            _TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _get(self, path: str, **kwargs) -> list[dict]:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json().get("data", [])
