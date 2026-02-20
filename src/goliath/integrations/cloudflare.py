"""
Cloudflare Integration — manage DNS, zones, Workers, and more via the Cloudflare API.

SETUP INSTRUCTIONS
==================

1. Log in to Cloudflare at https://dash.cloudflare.com/

2. Go to My Profile > API Tokens (https://dash.cloudflare.com/profile/api-tokens).

3. Create a token:
   - Option A (recommended): Click "Create Token" and use a template
     (e.g. "Edit zone DNS") or create a custom token with the permissions
     you need.
   - Option B: Use the Global API Key (less secure, grants full access).

4. Add to your .env:
     CLOUDFLARE_API_TOKEN=your-api-token

   Or for Global API Key:
     CLOUDFLARE_API_KEY=your-global-api-key
     CLOUDFLARE_EMAIL=your-email@example.com

IMPORTANT NOTES
===============
- API Token (Bearer) auth is preferred over Global API Key.
- API docs: https://developers.cloudflare.com/api/
- Rate limit: 1200 requests per 5 minutes.
- Zone ID can be found on the Overview page of each domain in the dashboard.

Usage:
    from goliath.integrations.cloudflare import CloudflareClient

    cf = CloudflareClient()

    # List zones (domains)
    zones = cf.list_zones()

    # Get zone details
    zone = cf.get_zone("zone-id-here")

    # List DNS records
    records = cf.list_dns_records("zone-id-here")

    # Create a DNS record
    record = cf.create_dns_record(
        zone_id="zone-id-here",
        type="A",
        name="app.example.com",
        content="192.0.2.1",
        proxied=True,
    )

    # Update a DNS record
    cf.update_dns_record(
        zone_id="zone-id-here",
        record_id="record-id",
        type="A",
        name="app.example.com",
        content="192.0.2.2",
    )

    # Delete a DNS record
    cf.delete_dns_record(zone_id="zone-id-here", record_id="record-id")

    # Purge cache
    cf.purge_cache(zone_id="zone-id-here")

    # List Workers
    workers = cf.list_workers(account_id="acct-id")
"""

import requests

from goliath import config

_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareClient:
    """Cloudflare REST API client for DNS, zones, Workers, and caching."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        if config.CLOUDFLARE_API_TOKEN:
            self.session.headers["Authorization"] = (
                f"Bearer {config.CLOUDFLARE_API_TOKEN}"
            )
        elif config.CLOUDFLARE_API_KEY and config.CLOUDFLARE_EMAIL:
            self.session.headers["X-Auth-Key"] = config.CLOUDFLARE_API_KEY
            self.session.headers["X-Auth-Email"] = config.CLOUDFLARE_EMAIL
        else:
            raise RuntimeError(
                "Cloudflare credentials not set. Either set CLOUDFLARE_API_TOKEN "
                "or both CLOUDFLARE_API_KEY and CLOUDFLARE_EMAIL in .env. "
                "See integrations/cloudflare.py for setup instructions."
            )

    # -- Zones -------------------------------------------------------------

    def list_zones(self, name: str | None = None, per_page: int = 50) -> list[dict]:
        """List zones (domains) in the account.

        Args:
            name:     Filter by domain name.
            per_page: Results per page (max 50).

        Returns:
            List of zone dicts.
        """
        params: dict = {"per_page": per_page}
        if name:
            params["name"] = name
        return self._get("/zones", params=params)

    def get_zone(self, zone_id: str) -> dict:
        """Get zone details.

        Args:
            zone_id: Zone ID.

        Returns:
            Zone dict.
        """
        return self._get_single(f"/zones/{zone_id}")

    # -- DNS Records -------------------------------------------------------

    def list_dns_records(
        self,
        zone_id: str,
        type: str | None = None,
        name: str | None = None,
        per_page: int = 100,
    ) -> list[dict]:
        """List DNS records for a zone.

        Args:
            zone_id:  Zone ID.
            type:     Filter by record type (A, AAAA, CNAME, MX, TXT, etc.).
            name:     Filter by record name.
            per_page: Results per page (max 100).

        Returns:
            List of DNS record dicts.
        """
        params: dict = {"per_page": per_page}
        if type:
            params["type"] = type
        if name:
            params["name"] = name
        return self._get(f"/zones/{zone_id}/dns_records", params=params)

    def create_dns_record(
        self,
        zone_id: str,
        type: str,
        name: str,
        content: str,
        ttl: int = 1,
        proxied: bool = False,
        **kwargs,
    ) -> dict:
        """Create a DNS record.

        Args:
            zone_id: Zone ID.
            type:    Record type (A, AAAA, CNAME, MX, TXT, etc.).
            name:    Record name (e.g. "app.example.com").
            content: Record value (e.g. "192.0.2.1").
            ttl:     Time to live in seconds (1 = automatic).
            proxied: Whether to proxy through Cloudflare.
            kwargs:  Additional fields (priority for MX, etc.).

        Returns:
            Created DNS record dict.
        """
        data: dict = {
            "type": type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied,
            **kwargs,
        }
        return self._post_single(f"/zones/{zone_id}/dns_records", json=data)

    def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        type: str,
        name: str,
        content: str,
        ttl: int = 1,
        proxied: bool = False,
        **kwargs,
    ) -> dict:
        """Update a DNS record.

        Args:
            zone_id:   Zone ID.
            record_id: DNS record ID.
            type:      Record type.
            name:      Record name.
            content:   Record value.
            ttl:       Time to live (1 = automatic).
            proxied:   Whether to proxy through Cloudflare.
            kwargs:    Additional fields.

        Returns:
            Updated DNS record dict.
        """
        data: dict = {
            "type": type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied,
            **kwargs,
        }
        resp = self.session.put(
            f"{_API_BASE}/zones/{zone_id}/dns_records/{record_id}", json=data
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    def delete_dns_record(self, zone_id: str, record_id: str) -> dict:
        """Delete a DNS record.

        Args:
            zone_id:   Zone ID.
            record_id: DNS record ID.

        Returns:
            Deletion result dict.
        """
        resp = self.session.delete(
            f"{_API_BASE}/zones/{zone_id}/dns_records/{record_id}"
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    # -- Cache -------------------------------------------------------------

    def purge_cache(
        self,
        zone_id: str,
        purge_everything: bool = True,
        files: list[str] | None = None,
    ) -> dict:
        """Purge cache for a zone.

        Args:
            zone_id:          Zone ID.
            purge_everything: Purge all cached content.
            files:            List of specific URLs to purge (overrides purge_everything).

        Returns:
            Purge result dict.
        """
        data: dict = {}
        if files:
            data["files"] = files
        else:
            data["purge_everything"] = purge_everything
        return self._post_single(f"/zones/{zone_id}/purge_cache", json=data)

    # -- Workers -----------------------------------------------------------

    def list_workers(self, account_id: str) -> list[dict]:
        """List Workers scripts.

        Args:
            account_id: Cloudflare account ID.

        Returns:
            List of Worker script dicts.
        """
        return self._get(f"/accounts/{account_id}/workers/scripts")

    def get_worker(self, account_id: str, script_name: str) -> dict:
        """Get a Worker script's metadata.

        Args:
            account_id:  Cloudflare account ID.
            script_name: Worker script name.

        Returns:
            Worker script metadata dict.
        """
        return self._get_single(
            f"/accounts/{account_id}/workers/scripts/{script_name}"
        )

    def delete_worker(self, account_id: str, script_name: str) -> dict:
        """Delete a Worker script.

        Args:
            account_id:  Cloudflare account ID.
            script_name: Worker script name.

        Returns:
            Deletion result dict.
        """
        resp = self.session.delete(
            f"{_API_BASE}/accounts/{account_id}/workers/scripts/{script_name}"
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    # -- Analytics ---------------------------------------------------------

    def get_zone_analytics(
        self,
        zone_id: str,
        since: str | None = None,
        until: str | None = None,
    ) -> dict:
        """Get zone analytics summary.

        Args:
            zone_id: Zone ID.
            since:   Start datetime (ISO 8601, e.g. "2025-01-01T00:00:00Z").
            until:   End datetime.

        Returns:
            Analytics summary dict.
        """
        params: dict = {}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        data = self._get(f"/zones/{zone_id}/analytics/dashboard", params=params)
        return data[0] if isinstance(data, list) and data else data

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> list[dict]:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json().get("result", [])

    def _get_single(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json().get("result", {})

    def _post_single(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json().get("result", {})
