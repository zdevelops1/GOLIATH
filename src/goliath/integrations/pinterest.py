"""
Pinterest Integration — create pins, manage boards, and browse via the Pinterest API v5.

SETUP INSTRUCTIONS
==================

1. Go to https://developers.pinterest.com/ and create an app.

2. Under your app settings, note the App ID and App Secret.

3. Generate an access token via OAuth 2.0:
   - Scopes needed: boards:read, boards:write, pins:read, pins:write
   - Use the Pinterest OAuth flow or the token generator in the dashboard.

4. Add to your .env:
     PINTEREST_ACCESS_TOKEN=your-access-token

IMPORTANT NOTES
===============
- Access tokens expire after 30 days. Use refresh tokens for long-lived access.
- Rate limit: 1,000 requests per minute per user token.
- Pin images must be publicly accessible URLs.
- Video pins require a business account.

Usage:
    from goliath.integrations.pinterest import PinterestClient

    pin = PinterestClient()

    # Create a pin
    pin.create_pin(board_id="123", title="My Pin", image_url="https://example.com/photo.jpg")

    # List your boards
    boards = pin.list_boards()

    # Search pins
    results = pin.search_pins("home decor")
"""

import requests

from goliath import config

_API_BASE = "https://api.pinterest.com/v5"


class PinterestClient:
    """Pinterest API v5 client for pins and boards."""

    def __init__(self):
        if not config.PINTEREST_ACCESS_TOKEN:
            raise RuntimeError(
                "PINTEREST_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/pinterest.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.PINTEREST_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- Pins --------------------------------------------------------------

    def create_pin(
        self,
        board_id: str,
        title: str = "",
        description: str = "",
        image_url: str | None = None,
        link: str | None = None,
        alt_text: str | None = None,
    ) -> dict:
        """Create a pin on a board.

        Args:
            board_id:    Board ID to pin to.
            title:       Pin title.
            description: Pin description.
            image_url:   Publicly accessible image URL.
            link:        Destination link URL.
            alt_text:    Alt text for accessibility.

        Returns:
            Created pin resource dict.
        """
        body: dict = {"board_id": board_id}
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        if link:
            body["link"] = link
        if alt_text:
            body["alt_text"] = alt_text
        if image_url:
            body["media_source"] = {"source_type": "image_url", "url": image_url}

        return self._post("/pins", json=body)

    def get_pin(self, pin_id: str) -> dict:
        """Get a pin by ID.

        Args:
            pin_id: Pinterest pin ID.

        Returns:
            Pin resource dict.
        """
        return self._get(f"/pins/{pin_id}")

    def delete_pin(self, pin_id: str) -> None:
        """Delete a pin.

        Args:
            pin_id: Pinterest pin ID.
        """
        resp = self.session.delete(f"{_API_BASE}/pins/{pin_id}")
        resp.raise_for_status()

    def save_pin(self, pin_id: str, board_id: str) -> dict:
        """Save (repin) an existing pin to a board.

        Args:
            pin_id:   Pin ID to save.
            board_id: Destination board ID.

        Returns:
            Saved pin resource dict.
        """
        return self._post(f"/pins/{pin_id}/save", json={"board_id": board_id})

    # -- Boards ------------------------------------------------------------

    def list_boards(self, page_size: int = 25) -> list[dict]:
        """List the authenticated user's boards.

        Args:
            page_size: Number of boards per page (1–250).

        Returns:
            List of board resource dicts.
        """
        return self._get("/boards", params={"page_size": page_size}).get("items", [])

    def create_board(
        self, name: str, description: str = "", privacy: str = "PUBLIC"
    ) -> dict:
        """Create a new board.

        Args:
            name:        Board name.
            description: Board description.
            privacy:     "PUBLIC" or "SECRET".

        Returns:
            Created board resource dict.
        """
        return self._post(
            "/boards",
            json={"name": name, "description": description, "privacy": privacy},
        )

    def delete_board(self, board_id: str) -> None:
        """Delete a board.

        Args:
            board_id: Pinterest board ID.
        """
        resp = self.session.delete(f"{_API_BASE}/boards/{board_id}")
        resp.raise_for_status()

    def get_board_pins(self, board_id: str, page_size: int = 25) -> list[dict]:
        """List pins on a board.

        Args:
            board_id:  Board ID.
            page_size: Number of pins per page (1–250).

        Returns:
            List of pin resource dicts.
        """
        return self._get(
            f"/boards/{board_id}/pins", params={"page_size": page_size}
        ).get("items", [])

    # -- Search ------------------------------------------------------------

    def search_pins(self, query: str, page_size: int = 25) -> list[dict]:
        """Search for pins.

        Args:
            query:     Search query.
            page_size: Number of results.

        Returns:
            List of pin resource dicts.
        """
        return self._get(
            "/search/pins", params={"query": query, "page_size": page_size}
        ).get("items", [])

    # -- User --------------------------------------------------------------

    def get_user(self) -> dict:
        """Get the authenticated user's profile.

        Returns:
            User account resource dict.
        """
        return self._get("/user_account")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
