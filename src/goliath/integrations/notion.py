"""
Notion Integration — manage pages, databases, and blocks via the Notion API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.notion.so/my-integrations
2. Click "New integration" and give it a name (e.g. "GOLIATH").
3. Select the workspace you want to connect.
4. Copy the "Internal Integration Secret" (starts with ntn_).
5. Add it to your .env:
     NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

6. Share pages/databases with the integration:
   - Open the page or database in Notion.
   - Click "..." (top right) > "Connections" > find your integration > "Connect".
   - The integration can only access pages it has been explicitly shared with.

Usage:
    from goliath.integrations.notion import NotionClient

    notion = NotionClient()

    # Search across the workspace
    results = notion.search("project plan")

    # Get a page
    page = notion.get_page("PAGE_ID")

    # Create a page in a database
    notion.create_page(
        parent_database_id="DATABASE_ID",
        properties={"Name": {"title": [{"text": {"content": "New task"}}]}},
    )

    # Query a database with filters
    rows = notion.query_database("DATABASE_ID", filter={
        "property": "Status",
        "select": {"equals": "In Progress"},
    })

    # Append content blocks to a page
    notion.append_blocks("PAGE_ID", children=[
        {"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello!"}}]}},
    ])
"""

import requests

from goliath import config

_BASE_URL = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Notion API client for pages, databases, and blocks."""

    def __init__(self):
        if not config.NOTION_API_KEY:
            raise RuntimeError(
                "NOTION_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/notion.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.NOTION_API_KEY}",
                "Content-Type": "application/json",
                "Notion-Version": _NOTION_VERSION,
            }
        )

    # -- Search ------------------------------------------------------------

    def search(
        self,
        query: str = "",
        filter_type: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Search across all shared pages and databases.

        Args:
            query:       Search text.
            filter_type: Optional filter — "page" or "database".
            page_size:   Max results (1–100).

        Returns:
            List of page/database result objects.
        """
        body: dict = {"page_size": page_size}
        if query:
            body["query"] = query
        if filter_type:
            body["filter"] = {"value": filter_type, "property": "object"}
        data = self._post("/search", json=body)
        return data.get("results", [])

    # -- Pages -------------------------------------------------------------

    def get_page(self, page_id: str) -> dict:
        """Retrieve a page by ID.

        Args:
            page_id: The Notion page ID (32-char hex, with or without dashes).

        Returns:
            Page object dict.
        """
        return self._get(f"/pages/{page_id}")

    def create_page(
        self,
        properties: dict,
        parent_database_id: str | None = None,
        parent_page_id: str | None = None,
        children: list[dict] | None = None,
    ) -> dict:
        """Create a new page.

        Must specify either parent_database_id (row in a database) or
        parent_page_id (sub-page).

        Args:
            properties:         Page properties dict (schema depends on parent DB).
            parent_database_id: Database to insert the page into.
            parent_page_id:     Parent page for a sub-page.
            children:           Optional initial block content.

        Returns:
            Created page object dict.
        """
        if not parent_database_id and not parent_page_id:
            raise ValueError("Specify parent_database_id or parent_page_id.")

        body: dict = {"properties": properties}
        if parent_database_id:
            body["parent"] = {"database_id": parent_database_id}
        else:
            body["parent"] = {"page_id": parent_page_id}
        if children:
            body["children"] = children

        return self._post("/pages", json=body)

    def update_page(self, page_id: str, properties: dict) -> dict:
        """Update a page's properties.

        Args:
            page_id:    The page ID to update.
            properties: Properties to update.

        Returns:
            Updated page object dict.
        """
        return self._patch(f"/pages/{page_id}", json={"properties": properties})

    # -- Databases ---------------------------------------------------------

    def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Query a database with optional filter and sorts.

        Args:
            database_id: The database ID.
            filter:      Notion filter object.
            sorts:       List of sort objects.
            page_size:   Max results per page.

        Returns:
            List of page objects (rows).
        """
        body: dict = {"page_size": page_size}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        data = self._post(f"/databases/{database_id}/query", json=body)
        return data.get("results", [])

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: dict,
    ) -> dict:
        """Create an inline database on a page.

        Args:
            parent_page_id: The page to create the database in.
            title:          Database title.
            properties:     Schema definition (e.g. {"Name": {"title": {}}, "Status": {"select": {}}}).

        Returns:
            Created database object dict.
        """
        return self._post(
            "/databases",
            json={
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "title": [{"type": "text", "text": {"content": title}}],
                "properties": properties,
            },
        )

    # -- Blocks ------------------------------------------------------------

    def get_block_children(self, block_id: str, page_size: int = 100) -> list[dict]:
        """Get the child blocks of a block or page.

        Args:
            block_id:  The block or page ID.
            page_size: Max results per page.

        Returns:
            List of block objects.
        """
        data = self._get(
            f"/blocks/{block_id}/children",
            params={"page_size": page_size},
        )
        return data.get("results", [])

    def append_blocks(self, block_id: str, children: list[dict]) -> dict:
        """Append child blocks to a page or block.

        Args:
            block_id: The parent page or block ID.
            children: List of block objects to append.

        Returns:
            Response dict with the appended block objects.
        """
        return self._patch(
            f"/blocks/{block_id}/children",
            json={"children": children},
        )

    def delete_block(self, block_id: str) -> dict:
        """Delete (archive) a block.

        Args:
            block_id: The block ID to delete.

        Returns:
            The deleted block object.
        """
        return self._delete(f"/blocks/{block_id}")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, **kwargs) -> dict:
        resp = self.session.patch(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, **kwargs) -> dict:
        resp = self.session.delete(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
