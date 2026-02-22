"""
Algolia Integration — manage indices and perform searches via the Algolia REST API.

SETUP INSTRUCTIONS
==================

1. Sign up or log in at https://www.algolia.com/

2. Go to Settings > API Keys (https://dashboard.algolia.com/account/api-keys/).

3. Copy your Application ID, Search-Only API Key, and Admin API Key.

4. Add to your .env:
     ALGOLIA_APP_ID=your-application-id
     ALGOLIA_API_KEY=your-admin-api-key

   (Use the Admin API key for write operations; for search-only, use Search key.)

IMPORTANT NOTES
===============
- API docs: https://www.algolia.com/doc/rest-api/search/
- Rate limits depend on your plan.
- Authentication via X-Algolia-API-Key and X-Algolia-Application-Id headers.
- Base URL: https://{app_id}.algolia.net

Usage:
    from goliath.integrations.algolia import AlgoliaClient

    alg = AlgoliaClient()

    # Search an index
    results = alg.search("products", query="laptop")

    # Add / update objects
    alg.save_objects("products", [
        {"objectID": "1", "name": "Laptop", "price": 999},
        {"objectID": "2", "name": "Mouse", "price": 29},
    ])

    # Get an object
    obj = alg.get_object("products", "1")

    # Delete an object
    alg.delete_object("products", "1")

    # List indices
    indices = alg.list_indices()

    # Clear an index
    alg.clear_index("products")
"""

import requests

from goliath import config


class AlgoliaClient:
    """Algolia REST API client for search and index management."""

    def __init__(self):
        if not config.ALGOLIA_APP_ID or not config.ALGOLIA_API_KEY:
            raise RuntimeError(
                "ALGOLIA_APP_ID and ALGOLIA_API_KEY must both be set. "
                "Add them to .env or export as environment variables. "
                "See integrations/algolia.py for setup instructions."
            )

        self.app_id = config.ALGOLIA_APP_ID
        self.base_url = f"https://{self.app_id}.algolia.net"

        self.session = requests.Session()
        self.session.headers.update({
            "X-Algolia-Application-Id": self.app_id,
            "X-Algolia-API-Key": config.ALGOLIA_API_KEY,
            "Content-Type": "application/json",
        })

    # -- Search ----------------------------------------------------------------

    def search(
        self,
        index_name: str,
        query: str = "",
        hits_per_page: int = 20,
        page: int = 0,
        filters: str | None = None,
        **kwargs,
    ) -> dict:
        """Search an index.

        Args:
            index_name:   Index to search.
            query:        Search query.
            hits_per_page: Results per page.
            page:         Page number (0-indexed).
            filters:      Filter string (e.g. "price > 100 AND category:laptop").
            kwargs:       Additional search parameters.

        Returns:
            Search result dict with "hits", "nbHits", "page", etc.
        """
        params: dict = {
            "query": query,
            "hitsPerPage": hits_per_page,
            "page": page,
            **kwargs,
        }
        if filters:
            params["filters"] = filters
        return self._post(
            f"/1/indexes/{index_name}/query", json={"params": _encode_params(params)}
        )

    def multi_search(self, queries: list[dict]) -> dict:
        """Search multiple indices in a single request.

        Args:
            queries: List of dicts with "indexName" and "params" keys.

        Returns:
            Dict with "results" list.
        """
        requests_payload = []
        for q in queries:
            entry: dict = {"indexName": q["indexName"]}
            if "params" in q:
                entry["params"] = _encode_params(q["params"])
            requests_payload.append(entry)
        return self._post(
            "/1/indexes/*/queries", json={"requests": requests_payload}
        )

    # -- Objects ---------------------------------------------------------------

    def get_object(
        self,
        index_name: str,
        object_id: str,
        attributes: list[str] | None = None,
    ) -> dict:
        """Get an object by ID.

        Args:
            index_name: Index name.
            object_id:  Object ID.
            attributes: Attributes to retrieve (omit for all).

        Returns:
            Object dict.
        """
        params: dict = {}
        if attributes:
            params["attributesToRetrieve"] = ",".join(attributes)
        return self._get(
            f"/1/indexes/{index_name}/{object_id}", params=params
        )

    def save_objects(
        self,
        index_name: str,
        objects: list[dict],
    ) -> dict:
        """Add or update objects in an index.

        Args:
            index_name: Index name.
            objects:    List of objects (each must have "objectID").

        Returns:
            Batch operation result.
        """
        requests_payload = [
            {"action": "addObject" if "objectID" not in obj else "updateObject",
             "body": obj}
            for obj in objects
        ]
        return self._post(
            f"/1/indexes/{index_name}/batch",
            json={"requests": requests_payload},
        )

    def delete_object(self, index_name: str, object_id: str) -> dict:
        """Delete an object from an index.

        Args:
            index_name: Index name.
            object_id:  Object ID.

        Returns:
            Deletion result.
        """
        resp = self.session.delete(
            f"{self.base_url}/1/indexes/{index_name}/{object_id}"
        )
        resp.raise_for_status()
        return resp.json()

    # -- Index Management ------------------------------------------------------

    def list_indices(self) -> list[dict]:
        """List all indices.

        Returns:
            List of index dicts.
        """
        data = self._get("/1/indexes")
        return data.get("items", [])

    def clear_index(self, index_name: str) -> dict:
        """Clear all objects from an index.

        Args:
            index_name: Index name.

        Returns:
            Clear operation result.
        """
        return self._post(f"/1/indexes/{index_name}/clear")

    def delete_index(self, index_name: str) -> dict:
        """Delete an index.

        Args:
            index_name: Index name.

        Returns:
            Deletion result.
        """
        resp = self.session.delete(
            f"{self.base_url}/1/indexes/{index_name}"
        )
        resp.raise_for_status()
        return resp.json()

    def get_settings(self, index_name: str) -> dict:
        """Get index settings.

        Args:
            index_name: Index name.

        Returns:
            Settings dict.
        """
        return self._get(f"/1/indexes/{index_name}/settings")

    def set_settings(self, index_name: str, settings: dict) -> dict:
        """Update index settings.

        Args:
            index_name: Index name.
            settings:   Settings dict.

        Returns:
            Update result.
        """
        resp = self.session.put(
            f"{self.base_url}/1/indexes/{index_name}/settings", json=settings
        )
        resp.raise_for_status()
        return resp.json()

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()


def _encode_params(params: dict) -> str:
    """Encode search parameters to Algolia's query-string format."""
    parts = []
    for key, val in params.items():
        if isinstance(val, bool):
            parts.append(f"{key}={'true' if val else 'false'}")
        elif isinstance(val, list):
            parts.append(f"{key}={','.join(str(v) for v in val)}")
        else:
            parts.append(f"{key}={val}")
    return "&".join(parts)
