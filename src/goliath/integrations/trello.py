"""
Trello Integration — manage boards, lists, and cards via the Trello REST API.

SETUP INSTRUCTIONS
==================

1. Log in to https://trello.com/

2. Get your API key from https://trello.com/power-ups/admin
   (Click on an existing Power-Up or create one, then find the API key.)

3. Generate a token by visiting:
   https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_API_KEY

4. Add to your .env:
     TRELLO_API_KEY=xxxxxxxxxxxxxxxx
     TRELLO_TOKEN=xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- API key + token are passed as query parameters (Trello's auth method).
- Rate limit: 300 requests/10 seconds per token, 100 requests/10 seconds per API key.
- Board IDs and card IDs are alphanumeric strings (e.g. "5a1b2c3d4e5f6g7h").
- API docs: https://developer.atlassian.com/cloud/trello/rest/

Usage:
    from goliath.integrations.trello import TrelloClient

    trello = TrelloClient()

    # List boards
    boards = trello.list_boards()

    # Get lists on a board
    lists = trello.get_lists(board_id="abc123")

    # Create a card
    card = trello.create_card(list_id="xyz789", name="New task", desc="Details here")

    # Move a card to a different list
    trello.update_card(card_id="card123", list_id="newlist456")

    # Add a comment to a card
    trello.add_comment(card_id="card123", text="Working on it!")
"""

import requests

from goliath import config

_API_BASE = "https://api.trello.com/1"


class TrelloClient:
    """Trello REST API client for boards, lists, and cards."""

    def __init__(self):
        if not config.TRELLO_API_KEY:
            raise RuntimeError(
                "TRELLO_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/trello.py for setup instructions."
            )
        if not config.TRELLO_TOKEN:
            raise RuntimeError(
                "TRELLO_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/trello.py for setup instructions."
            )

        self._auth = {
            "key": config.TRELLO_API_KEY,
            "token": config.TRELLO_TOKEN,
        }
        self.session = requests.Session()

    # -- Boards ------------------------------------------------------------

    def list_boards(self, member: str = "me") -> list[dict]:
        """List boards for a member.

        Args:
            member: Member ID or "me" for the token owner.

        Returns:
            List of board dicts.
        """
        return self._get(f"/members/{member}/boards")

    def get_board(self, board_id: str) -> dict:
        """Get a board by ID.

        Args:
            board_id: Trello board ID.

        Returns:
            Board dict.
        """
        return self._get(f"/boards/{board_id}")

    def create_board(self, name: str, **kwargs) -> dict:
        """Create a new board.

        Args:
            name:   Board name.
            kwargs: Additional fields (desc, defaultLists, idOrganization, etc.).

        Returns:
            Created board dict.
        """
        return self._post("/boards", params={"name": name, **kwargs})

    # -- Lists -------------------------------------------------------------

    def get_lists(self, board_id: str) -> list[dict]:
        """Get all lists on a board.

        Args:
            board_id: Trello board ID.

        Returns:
            List of list dicts.
        """
        return self._get(f"/boards/{board_id}/lists")

    def create_list(self, board_id: str, name: str) -> dict:
        """Create a list on a board.

        Args:
            board_id: Trello board ID.
            name:     List name.

        Returns:
            Created list dict.
        """
        return self._post("/lists", params={"name": name, "idBoard": board_id})

    # -- Cards -------------------------------------------------------------

    def get_cards(self, list_id: str) -> list[dict]:
        """Get all cards in a list.

        Args:
            list_id: Trello list ID.

        Returns:
            List of card dicts.
        """
        return self._get(f"/lists/{list_id}/cards")

    def get_card(self, card_id: str) -> dict:
        """Get a card by ID.

        Args:
            card_id: Trello card ID.

        Returns:
            Card dict.
        """
        return self._get(f"/cards/{card_id}")

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str | None = None,
        due: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Create a card.

        Args:
            list_id: Trello list ID to add the card to.
            name:    Card name/title.
            desc:    Card description (Markdown supported).
            due:     Due date (ISO 8601 string).
            labels:  List of label IDs.
            kwargs:  Additional fields (pos, idMembers, etc.).

        Returns:
            Created card dict.
        """
        params: dict = {"idList": list_id, "name": name, **kwargs}
        if desc:
            params["desc"] = desc
        if due:
            params["due"] = due
        if labels:
            params["idLabels"] = ",".join(labels)
        return self._post("/cards", params=params)

    def update_card(self, card_id: str, **kwargs) -> dict:
        """Update a card.

        Args:
            card_id: Trello card ID.
            kwargs:  Fields to update (name, desc, due, idList, closed, etc.).

        Returns:
            Updated card dict.
        """
        return self._put(f"/cards/{card_id}", params=kwargs)

    def delete_card(self, card_id: str) -> None:
        """Delete a card.

        Args:
            card_id: Trello card ID.
        """
        resp = self.session.delete(
            f"{_API_BASE}/cards/{card_id}",
            params=self._auth,
        )
        resp.raise_for_status()

    def add_comment(self, card_id: str, text: str) -> dict:
        """Add a comment to a card.

        Args:
            card_id: Trello card ID.
            text:    Comment text.

        Returns:
            Created comment (action) dict.
        """
        return self._post(f"/cards/{card_id}/actions/comments", params={"text": text})

    # -- Labels ------------------------------------------------------------

    def get_labels(self, board_id: str) -> list[dict]:
        """Get all labels on a board.

        Args:
            board_id: Trello board ID.

        Returns:
            List of label dicts.
        """
        return self._get(f"/boards/{board_id}/labels")

    # -- Checklists --------------------------------------------------------

    def create_checklist(self, card_id: str, name: str) -> dict:
        """Create a checklist on a card.

        Args:
            card_id: Trello card ID.
            name:    Checklist name.

        Returns:
            Created checklist dict.
        """
        return self._post("/checklists", params={"idCard": card_id, "name": name})

    def add_checklist_item(self, checklist_id: str, name: str) -> dict:
        """Add an item to a checklist.

        Args:
            checklist_id: Trello checklist ID.
            name:         Item name/text.

        Returns:
            Created checklist item dict.
        """
        return self._post(
            f"/checklists/{checklist_id}/checkItems", params={"name": name}
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        all_params = {**self._auth, **(params or {})}
        resp = self.session.get(f"{_API_BASE}{path}", params=all_params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, params: dict | None = None, **kwargs) -> dict:
        all_params = {**self._auth, **(params or {})}
        resp = self.session.post(f"{_API_BASE}{path}", params=all_params, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, params: dict | None = None) -> dict:
        all_params = {**self._auth, **(params or {})}
        resp = self.session.put(f"{_API_BASE}{path}", params=all_params)
        resp.raise_for_status()
        return resp.json()
