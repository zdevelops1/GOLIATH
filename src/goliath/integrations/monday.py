"""
Monday.com Integration — manage boards, items, and updates via the Monday.com GraphQL API.

SETUP INSTRUCTIONS
==================

1. Log in to Monday.com at https://monday.com/

2. Click your avatar (bottom-left) > Developers > My Access Tokens.
   Or go directly to: https://monday.com/apps/manage

3. Click "Show" to reveal your API token, or generate a new one.

4. Add it to your .env:
     MONDAY_API_TOKEN=eyJhbGciOiJIUzI1NiJ9...

IMPORTANT NOTES
===============
- Monday.com uses a GraphQL API (not REST).
- API docs: https://developer.monday.com/api-reference
- Rate limit: 5,000,000 complexity points per minute.
- All queries go through a single endpoint: https://api.monday.com/v2

Usage:
    from goliath.integrations.monday import MondayClient

    mon = MondayClient()

    # List boards
    boards = mon.list_boards()

    # Get a specific board with its items
    board = mon.get_board(board_id="123456")

    # Create an item (row) on a board
    item = mon.create_item(
        board_id="123456",
        item_name="New feature request",
        column_values={"status": "Working on it", "date4": "2025-03-01"},
    )

    # Update column values
    mon.update_item(board_id="123456", item_id="789", column_values={"status": "Done"})

    # Add an update (comment) to an item
    mon.add_update(item_id="789", body="Shipped in v2.3!")

    # Create a board
    board = mon.create_board(name="Sprint 12", board_kind="public")
"""

import json

import requests

from goliath import config

_API_URL = "https://api.monday.com/v2"


class MondayClient:
    """Monday.com GraphQL API client for boards, items, and updates."""

    def __init__(self):
        if not config.MONDAY_API_TOKEN:
            raise RuntimeError(
                "MONDAY_API_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/monday.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": config.MONDAY_API_TOKEN,
            "Content-Type": "application/json",
        })

    # -- Boards ------------------------------------------------------------

    def list_boards(self, limit: int = 25) -> list[dict]:
        """List boards.

        Args:
            limit: Max number of boards to return.

        Returns:
            List of board dicts with id, name, and state.
        """
        query = f"{{ boards(limit: {limit}) {{ id name state board_kind }} }}"
        return self._query(query)["boards"]

    def get_board(self, board_id: str) -> dict:
        """Get a board with its columns and items.

        Args:
            board_id: Board ID.

        Returns:
            Board dict with columns and items.
        """
        query = (
            "{ boards(ids: [%s]) { id name columns { id title type } "
            "items_page(limit: 100) { items { id name column_values { id text value } } } } }"
            % board_id
        )
        boards = self._query(query)["boards"]
        return boards[0] if boards else {}

    def create_board(
        self,
        name: str,
        board_kind: str = "public",
        workspace_id: int | None = None,
    ) -> dict:
        """Create a new board.

        Args:
            name:         Board name.
            board_kind:   "public", "private", or "share".
            workspace_id: Optional workspace ID.

        Returns:
            Created board dict with id.
        """
        ws_arg = f", workspace_id: {workspace_id}" if workspace_id else ""
        query = (
            'mutation { create_board(board_name: "%s", board_kind: %s%s) { id } }'
            % (name.replace('"', '\\"'), board_kind, ws_arg)
        )
        return self._query(query)["create_board"]

    # -- Items -------------------------------------------------------------

    def create_item(
        self,
        board_id: str,
        item_name: str,
        group_id: str | None = None,
        column_values: dict | None = None,
    ) -> dict:
        """Create an item (row) on a board.

        Args:
            board_id:      Board ID.
            item_name:     Item name.
            group_id:      Optional group ID within the board.
            column_values: Dict mapping column IDs to values.

        Returns:
            Created item dict with id.
        """
        cv_arg = ""
        if column_values:
            cv_json = json.dumps(json.dumps(column_values))
            cv_arg = f", column_values: {cv_json}"
        group_arg = f', group_id: "{group_id}"' if group_id else ""

        query = (
            'mutation { create_item(board_id: %s, item_name: "%s"%s%s) { id name } }'
            % (board_id, item_name.replace('"', '\\"'), group_arg, cv_arg)
        )
        return self._query(query)["create_item"]

    def update_item(
        self,
        board_id: str,
        item_id: str,
        column_values: dict,
    ) -> dict:
        """Update column values on an item.

        Args:
            board_id:      Board ID.
            item_id:       Item ID.
            column_values: Dict mapping column IDs to new values.

        Returns:
            Updated item dict with id.
        """
        cv_json = json.dumps(json.dumps(column_values))
        query = (
            "mutation { change_multiple_column_values("
            "board_id: %s, item_id: %s, column_values: %s) { id } }"
            % (board_id, item_id, cv_json)
        )
        return self._query(query)["change_multiple_column_values"]

    def get_item(self, item_id: str) -> dict:
        """Get an item by ID.

        Args:
            item_id: Item ID.

        Returns:
            Item dict with name, column values, and updates.
        """
        query = (
            "{ items(ids: [%s]) { id name column_values { id text value } "
            "updates { id body created_at } } }" % item_id
        )
        items = self._query(query)["items"]
        return items[0] if items else {}

    def delete_item(self, item_id: str) -> dict:
        """Delete an item.

        Args:
            item_id: Item ID.

        Returns:
            Deleted item dict with id.
        """
        query = "mutation { delete_item(item_id: %s) { id } }" % item_id
        return self._query(query)["delete_item"]

    # -- Updates (comments) ------------------------------------------------

    def add_update(self, item_id: str, body: str) -> dict:
        """Add an update (comment) to an item.

        Args:
            item_id: Item ID.
            body:    Update body text.

        Returns:
            Created update dict with id.
        """
        escaped = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        query = (
            'mutation { create_update(item_id: %s, body: "%s") { id body created_at } }'
            % (item_id, escaped)
        )
        return self._query(query)["create_update"]

    # -- internal helpers --------------------------------------------------

    def _query(self, query: str) -> dict:
        """Execute a GraphQL query against the Monday.com API."""
        resp = self.session.post(_API_URL, json={"query": query})
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Monday.com API error: {body['errors']}")
        return body.get("data", body)
