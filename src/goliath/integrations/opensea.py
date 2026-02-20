"""
OpenSea Integration — browse NFT collections, assets, and events via the OpenSea API.

SETUP INSTRUCTIONS
==================

1. Go to https://opensea.io/ and create an account.

2. Request an API key at https://docs.opensea.io/reference/api-keys

3. Copy your API key.

4. Add to your .env:
     OPENSEA_API_KEY=your_api_key_here

IMPORTANT NOTES
===============
- API docs: https://docs.opensea.io/reference/api-overview
- Free tier: 4 requests/second.
- The API provides read-only access to NFT data (no buying/selling).
- Supports Ethereum, Polygon, Arbitrum, and other chains.
- Collection slugs are used as identifiers (e.g. "boredapeyachtclub").

Usage:
    from goliath.integrations.opensea import OpenSeaClient

    os_client = OpenSeaClient()

    # Get a collection
    collection = os_client.get_collection("boredapeyachtclub")

    # List collections
    collections = os_client.list_collections(chain="ethereum", limit=10)

    # Get NFTs in a collection
    nfts = os_client.get_nfts(collection_slug="boredapeyachtclub")

    # Get a specific NFT
    nft = os_client.get_nft(chain="ethereum", address="0xBC4CA0...", token_id="1")

    # Get collection stats
    stats = os_client.get_collection_stats("boredapeyachtclub")

    # List events (sales, transfers, etc.)
    events = os_client.list_events(collection_slug="boredapeyachtclub", event_type="sale")

    # Get best offer / listing
    offers = os_client.get_best_offer(collection_slug="boredapeyachtclub", token_id="1")
"""

import requests

from goliath import config

_API_BASE = "https://api.opensea.io/api/v2"


class OpenSeaClient:
    """OpenSea API client for browsing NFT collections, assets, and events."""

    def __init__(self):
        if not config.OPENSEA_API_KEY:
            raise RuntimeError(
                "OPENSEA_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/opensea.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-API-KEY": config.OPENSEA_API_KEY,
            "Accept": "application/json",
        })

    # -- Collections -------------------------------------------------------

    def get_collection(self, collection_slug: str) -> dict:
        """Get details about a collection.

        Args:
            collection_slug: Collection slug (e.g. "boredapeyachtclub").

        Returns:
            Collection detail dict.
        """
        return self._get(f"/collections/{collection_slug}")

    def list_collections(
        self,
        chain: str | None = None,
        limit: int = 50,
        next_cursor: str | None = None,
    ) -> dict:
        """List collections.

        Args:
            chain:       Chain identifier (e.g. "ethereum", "polygon").
            limit:       Number of results (max 100).
            next_cursor: Cursor for pagination.

        Returns:
            Dict with "collections" list and "next" cursor.
        """
        params: dict = {"limit": limit}
        if chain:
            params["chain"] = chain
        if next_cursor:
            params["next"] = next_cursor
        return self._get("/collections", params=params)

    def get_collection_stats(self, collection_slug: str) -> dict:
        """Get collection statistics (floor price, volume, etc.).

        Args:
            collection_slug: Collection slug.

        Returns:
            Stats dict with total volume, floor price, num owners, etc.
        """
        return self._get(f"/collections/{collection_slug}/stats")

    # -- NFTs --------------------------------------------------------------

    def get_nfts(
        self,
        collection_slug: str,
        limit: int = 50,
        next_cursor: str | None = None,
    ) -> dict:
        """Get NFTs in a collection.

        Args:
            collection_slug: Collection slug.
            limit:           Number of results (max 200).
            next_cursor:     Cursor for pagination.

        Returns:
            Dict with "nfts" list and "next" cursor.
        """
        params: dict = {"limit": limit}
        if next_cursor:
            params["next"] = next_cursor
        return self._get(f"/collection/{collection_slug}/nfts", params=params)

    def get_nft(self, chain: str, address: str, token_id: str) -> dict:
        """Get a specific NFT.

        Args:
            chain:    Chain identifier (e.g. "ethereum").
            address:  Contract address.
            token_id: Token ID.

        Returns:
            NFT detail dict.
        """
        return self._get(f"/chain/{chain}/contract/{address}/nfts/{token_id}")

    def get_nfts_by_account(
        self,
        address: str,
        chain: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Get NFTs owned by an account.

        Args:
            address: Wallet address.
            chain:   Optional chain filter.
            limit:   Number of results.

        Returns:
            Dict with "nfts" list.
        """
        params: dict = {"limit": limit}
        if chain:
            params["chain"] = chain
        return self._get(f"/chain/ethereum/account/{address}/nfts", params=params)

    # -- Events ------------------------------------------------------------

    def list_events(
        self,
        collection_slug: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        next_cursor: str | None = None,
    ) -> dict:
        """List NFT events (sales, transfers, listings, etc.).

        Args:
            collection_slug: Filter by collection.
            event_type:      Event type ("sale", "transfer", "listing", "offer", "cancel").
            limit:           Number of results.
            next_cursor:     Cursor for pagination.

        Returns:
            Dict with "asset_events" list and "next" cursor.
        """
        params: dict = {"limit": limit}
        if collection_slug:
            params["collection_slug"] = collection_slug
        if event_type:
            params["event_type"] = event_type
        if next_cursor:
            params["next"] = next_cursor
        return self._get("/events", params=params)

    # -- Orders / Offers ---------------------------------------------------

    def get_best_offer(self, collection_slug: str, token_id: str) -> dict:
        """Get the best offer for an NFT.

        Args:
            collection_slug: Collection slug.
            token_id:        Token ID.

        Returns:
            Best offer dict.
        """
        return self._get(f"/offers/collection/{collection_slug}/nfts/{token_id}/best")

    def get_best_listing(self, collection_slug: str, token_id: str) -> dict:
        """Get the best listing for an NFT.

        Args:
            collection_slug: Collection slug.
            token_id:        Token ID.

        Returns:
            Best listing dict.
        """
        return self._get(f"/listings/collection/{collection_slug}/nfts/{token_id}/best")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
