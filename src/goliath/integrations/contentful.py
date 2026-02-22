"""
Contentful Integration — manage content entries, assets, and spaces via the Contentful API.

SETUP INSTRUCTIONS
==================

1. Log in to Contentful at https://app.contentful.com/

2. Go to Settings > API Keys for your space.

3. Create a new API key or use an existing one. You'll need:
   - Space ID (shown at the top of Settings)
   - Content Delivery API (CDA) access token (for published content)
   - Content Management API (CMA) token (for creating/editing content):
     Go to Settings > CMA tokens > Generate personal token.

4. Add to your .env:
     CONTENTFUL_SPACE_ID=your-space-id
     CONTENTFUL_ACCESS_TOKEN=your-cda-access-token
     CONTENTFUL_MANAGEMENT_TOKEN=your-cma-token

IMPORTANT NOTES
===============
- CDA (read): https://cdn.contentful.com
- CMA (write): https://api.contentful.com
- Preview API: https://preview.contentful.com
- API docs: https://www.contentful.com/developers/docs/references/
- Rate limits: CDA 78 req/sec, CMA 10 req/sec.

Usage:
    from goliath.integrations.contentful import ContentfulClient

    cf = ContentfulClient()

    # List entries
    entries = cf.list_entries()

    # Get a single entry
    entry = cf.get_entry("entry-id")

    # Search entries by content type
    posts = cf.list_entries(content_type="blogPost")

    # List assets
    assets = cf.list_assets()

    # Get content types
    types = cf.list_content_types()

    # Create an entry (requires management token)
    entry = cf.create_entry("blogPost", fields={
        "title": {"en-US": "My Post"},
        "body": {"en-US": "Hello world."},
    })

    # Update an entry
    cf.update_entry("entry-id", version=1, fields={
        "title": {"en-US": "Updated Title"},
    })

    # Publish an entry
    cf.publish_entry("entry-id", version=2)
"""

import requests

from goliath import config

_CDA_BASE = "https://cdn.contentful.com"
_CMA_BASE = "https://api.contentful.com"


class ContentfulClient:
    """Contentful API client for content entries, assets, and spaces."""

    def __init__(self):
        if not config.CONTENTFUL_SPACE_ID:
            raise RuntimeError(
                "CONTENTFUL_SPACE_ID is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/contentful.py for setup instructions."
            )
        if not config.CONTENTFUL_ACCESS_TOKEN:
            raise RuntimeError(
                "CONTENTFUL_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/contentful.py for setup instructions."
            )

        self.space_id = config.CONTENTFUL_SPACE_ID
        self._cda_token = config.CONTENTFUL_ACCESS_TOKEN
        self._cma_token = (
            getattr(config, "CONTENTFUL_MANAGEMENT_TOKEN", "") or ""
        )

        # CDA session (read)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self._cda_token}",
            "Content-Type": "application/json",
        })

        # CMA session (write) — set up only if token is available
        self._cma_session = requests.Session()
        if self._cma_token:
            self._cma_session.headers.update({
                "Authorization": f"Bearer {self._cma_token}",
                "Content-Type": "application/vnd.contentful.management.v1+json",
            })

    # -- Entries (read) --------------------------------------------------------

    def list_entries(
        self,
        content_type: str | None = None,
        limit: int = 100,
        skip: int = 0,
        query: dict | None = None,
    ) -> list[dict]:
        """List entries from the CDA.

        Args:
            content_type: Filter by content type ID.
            limit:        Max results (max 1000).
            skip:         Number of results to skip.
            query:        Additional query params.

        Returns:
            List of entry dicts.
        """
        params: dict = {"limit": limit, "skip": skip}
        if content_type:
            params["content_type"] = content_type
        if query:
            params.update(query)

        data = self._cda_get(f"/spaces/{self.space_id}/entries", params=params)
        return data.get("items", [])

    def get_entry(self, entry_id: str) -> dict:
        """Get a single entry.

        Args:
            entry_id: Entry ID.

        Returns:
            Entry dict.
        """
        return self._cda_get(f"/spaces/{self.space_id}/entries/{entry_id}")

    # -- Assets ----------------------------------------------------------------

    def list_assets(self, limit: int = 100, skip: int = 0) -> list[dict]:
        """List assets.

        Args:
            limit: Max results.
            skip:  Offset.

        Returns:
            List of asset dicts.
        """
        data = self._cda_get(
            f"/spaces/{self.space_id}/assets",
            params={"limit": limit, "skip": skip},
        )
        return data.get("items", [])

    def get_asset(self, asset_id: str) -> dict:
        """Get asset details.

        Args:
            asset_id: Asset ID.

        Returns:
            Asset dict.
        """
        return self._cda_get(f"/spaces/{self.space_id}/assets/{asset_id}")

    # -- Content Types ---------------------------------------------------------

    def list_content_types(self) -> list[dict]:
        """List content types for the space.

        Returns:
            List of content type dicts.
        """
        data = self._cda_get(f"/spaces/{self.space_id}/content_types")
        return data.get("items", [])

    # -- Management (write) ----------------------------------------------------

    def create_entry(
        self,
        content_type_id: str,
        fields: dict,
        environment: str = "master",
    ) -> dict:
        """Create an entry (requires management token).

        Args:
            content_type_id: Content type ID.
            fields:          Fields dict (localized, e.g. {"title": {"en-US": "Hi"}}).
            environment:     Environment ID.

        Returns:
            Created entry dict.
        """
        self._require_cma()
        resp = self._cma_session.post(
            f"{_CMA_BASE}/spaces/{self.space_id}/environments/{environment}/entries",
            headers={"X-Contentful-Content-Type": content_type_id},
            json={"fields": fields},
        )
        resp.raise_for_status()
        return resp.json()

    def update_entry(
        self,
        entry_id: str,
        version: int,
        fields: dict,
        environment: str = "master",
    ) -> dict:
        """Update an entry.

        Args:
            entry_id:    Entry ID.
            version:     Current entry version (for optimistic locking).
            fields:      Updated fields dict.
            environment: Environment ID.

        Returns:
            Updated entry dict.
        """
        self._require_cma()
        resp = self._cma_session.put(
            f"{_CMA_BASE}/spaces/{self.space_id}/environments/{environment}"
            f"/entries/{entry_id}",
            headers={"X-Contentful-Version": str(version)},
            json={"fields": fields},
        )
        resp.raise_for_status()
        return resp.json()

    def publish_entry(
        self,
        entry_id: str,
        version: int,
        environment: str = "master",
    ) -> dict:
        """Publish an entry.

        Args:
            entry_id:    Entry ID.
            version:     Current entry version.
            environment: Environment ID.

        Returns:
            Published entry dict.
        """
        self._require_cma()
        resp = self._cma_session.put(
            f"{_CMA_BASE}/spaces/{self.space_id}/environments/{environment}"
            f"/entries/{entry_id}/published",
            headers={"X-Contentful-Version": str(version)},
        )
        resp.raise_for_status()
        return resp.json()

    def unpublish_entry(
        self,
        entry_id: str,
        environment: str = "master",
    ) -> dict:
        """Unpublish an entry.

        Args:
            entry_id:    Entry ID.
            environment: Environment ID.

        Returns:
            Unpublished entry dict.
        """
        self._require_cma()
        resp = self._cma_session.delete(
            f"{_CMA_BASE}/spaces/{self.space_id}/environments/{environment}"
            f"/entries/{entry_id}/published",
        )
        resp.raise_for_status()
        return resp.json()

    # -- internal helpers ------------------------------------------------------

    def _require_cma(self):
        if not self._cma_token:
            raise RuntimeError(
                "CONTENTFUL_MANAGEMENT_TOKEN is required for write operations. "
                "Add it to .env."
            )

    def _cda_get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_CDA_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
