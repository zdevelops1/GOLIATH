"""
Webflow Integration — manage sites, CMS collections, and items via the Webflow Data API v2.

SETUP INSTRUCTIONS
==================

1. Log in to Webflow at https://webflow.com

2. Go to Site Settings > Apps & Integrations > API Access (or Workspace
   Settings for workspace-level tokens).

3. Generate an API token:
   - Site-level: Settings > Apps & Integrations > Generate API Token
   - Workspace-level: Workspace Settings > API Access > Generate Token

4. Required scopes: sites:read, cms:read, cms:write

5. Add to your .env:
     WEBFLOW_ACCESS_TOKEN=your-api-token

IMPORTANT NOTES
===============
- Webflow API v2 uses Bearer token auth.
- Rate limit: 60 requests per minute.
- CMS items must conform to the collection's schema (field types matter).
- Publishing changes requires a separate publish call.
- Item slugs must be unique within a collection.

Usage:
    from goliath.integrations.webflow import WebflowClient

    wf = WebflowClient()

    # List sites
    sites = wf.list_sites()

    # List collections in a site
    collections = wf.list_collections(site_id="site_abc")

    # List items in a collection
    items = wf.list_items(collection_id="col_abc")

    # Create a CMS item
    wf.create_item(collection_id="col_abc", fields={"name": "New Post", "slug": "new-post"})

    # Publish a site
    wf.publish_site(site_id="site_abc")
"""

import requests

from goliath import config

_API_BASE = "https://api.webflow.com/v2"


class WebflowClient:
    """Webflow Data API v2 client for sites and CMS management."""

    def __init__(self):
        if not config.WEBFLOW_ACCESS_TOKEN:
            raise RuntimeError(
                "WEBFLOW_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/webflow.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.WEBFLOW_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- Sites -------------------------------------------------------------

    def list_sites(self) -> list[dict]:
        """List all sites in the workspace.

        Returns:
            List of site resource dicts.
        """
        return self._get("/sites").get("sites", [])

    def get_site(self, site_id: str) -> dict:
        """Get a site by ID.

        Args:
            site_id: Webflow site ID.

        Returns:
            Site resource dict.
        """
        return self._get(f"/sites/{site_id}")

    def publish_site(self, site_id: str, domain_names: list[str] | None = None) -> dict:
        """Publish a site to its domains.

        Args:
            site_id:      Webflow site ID.
            domain_names: Optional list of domains to publish to.
                          None = all configured domains.

        Returns:
            Publish response dict.
        """
        body: dict = {}
        if domain_names:
            body["customDomains"] = domain_names
        return self._post(f"/sites/{site_id}/publish", json=body)

    # -- Collections -------------------------------------------------------

    def list_collections(self, site_id: str) -> list[dict]:
        """List CMS collections for a site.

        Args:
            site_id: Webflow site ID.

        Returns:
            List of collection resource dicts.
        """
        return self._get(f"/sites/{site_id}/collections").get("collections", [])

    def get_collection(self, collection_id: str) -> dict:
        """Get a collection by ID.

        Args:
            collection_id: Webflow collection ID.

        Returns:
            Collection resource dict with field definitions.
        """
        return self._get(f"/collections/{collection_id}")

    # -- Items -------------------------------------------------------------

    def list_items(
        self, collection_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """List items in a collection.

        Args:
            collection_id: Webflow collection ID.
            limit:         Number of items (1–100).
            offset:        Pagination offset.

        Returns:
            List of item resource dicts.
        """
        return self._get(
            f"/collections/{collection_id}/items",
            params={"limit": limit, "offset": offset},
        ).get("items", [])

    def get_item(self, collection_id: str, item_id: str) -> dict:
        """Get a single item.

        Args:
            collection_id: Webflow collection ID.
            item_id:       Item ID.

        Returns:
            Item resource dict.
        """
        return self._get(f"/collections/{collection_id}/items/{item_id}")

    def create_item(
        self,
        collection_id: str,
        fields: dict,
        is_draft: bool = False,
    ) -> dict:
        """Create a new CMS item.

        Args:
            collection_id: Webflow collection ID.
            fields:        Field values dict matching the collection schema.
            is_draft:      True to save as draft.

        Returns:
            Created item resource dict.
        """
        body: dict = {"fieldData": fields, "isDraft": is_draft}
        return self._post(f"/collections/{collection_id}/items", json=body)

    def update_item(self, collection_id: str, item_id: str, fields: dict) -> dict:
        """Update a CMS item.

        Args:
            collection_id: Webflow collection ID.
            item_id:       Item ID.
            fields:        Fields to update.

        Returns:
            Updated item resource dict.
        """
        return self._patch(
            f"/collections/{collection_id}/items/{item_id}",
            json={"fieldData": fields},
        )

    def delete_item(self, collection_id: str, item_id: str) -> None:
        """Delete a CMS item.

        Args:
            collection_id: Webflow collection ID.
            item_id:       Item ID.
        """
        resp = self.session.delete(
            f"{_API_BASE}/collections/{collection_id}/items/{item_id}"
        )
        resp.raise_for_status()

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

    def _patch(self, path: str, **kwargs) -> dict:
        resp = self.session.patch(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
