"""
Snapchat Integration — manage ads, media, and campaigns via the Snapchat Marketing API.

SETUP INSTRUCTIONS
==================

1. Go to https://business.snapchat.com/ and log in.

2. Navigate to Business Manager > Business Settings > Snap Kit Apps,
   or visit https://kit.snapchat.com/portal/ to register an app.

3. Under your app, go to the Marketing API section and request access.

4. Once approved, generate an OAuth2 access token using the authorization
   code flow. You'll need:
   - Client ID and Client Secret from your app settings
   - A refresh token obtained via the OAuth flow

5. Add to your .env:
     SNAPCHAT_ACCESS_TOKEN=your_oauth_access_token
     SNAPCHAT_AD_ACCOUNT_ID=your_ad_account_id  (optional, for ad management)

IMPORTANT NOTES
===============
- Authentication uses OAuth2 Bearer tokens.
- Marketing API docs: https://marketingapi.snapchat.com/docs/
- Rate limit: varies by endpoint; typically 1000 requests per minute.
- The Marketing API is primarily for ad management and campaign analytics.
- For organic content (Snap Kit), different SDKs are required.

Usage:
    from goliath.integrations.snapchat import SnapchatClient

    snap = SnapchatClient()

    # Get authenticated user info
    me = snap.get_me()

    # List ad accounts
    accounts = snap.list_ad_accounts(org_id="org-id-here")

    # List campaigns
    campaigns = snap.list_campaigns(ad_account_id="acct-id")

    # Create a campaign
    campaign = snap.create_campaign(
        ad_account_id="acct-id",
        name="Summer Sale",
        status="PAUSED",
        objective="AWARENESS",
    )

    # Get campaign stats
    stats = snap.get_campaign_stats(campaign_id="camp-id")

    # List ad squads (ad sets)
    squads = snap.list_ad_squads(campaign_id="camp-id")

    # Upload creative media
    media = snap.create_media(ad_account_id="acct-id", name="Video Ad", type="VIDEO")
"""

import requests

from goliath import config

_API_BASE = "https://adsapi.snapchat.com/v1"


class SnapchatClient:
    """Snapchat Marketing API client for ads, campaigns, and media."""

    def __init__(self):
        if not config.SNAPCHAT_ACCESS_TOKEN:
            raise RuntimeError(
                "SNAPCHAT_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/snapchat.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.SNAPCHAT_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })
        self.ad_account_id = config.SNAPCHAT_AD_ACCOUNT_ID

    # -- User / Org --------------------------------------------------------

    def get_me(self) -> dict:
        """Get authenticated user info.

        Returns:
            User dict with id, display_name, email, etc.
        """
        return self._get("/me").get("me", {})

    def list_organizations(self) -> list[dict]:
        """List organizations the user belongs to.

        Returns:
            List of organization dicts.
        """
        return self._get("/me/organizations").get("organizations", [])

    # -- Ad Accounts -------------------------------------------------------

    def list_ad_accounts(self, org_id: str) -> list[dict]:
        """List ad accounts in an organization.

        Args:
            org_id: Organization ID.

        Returns:
            List of ad account dicts.
        """
        data = self._get(f"/organizations/{org_id}/adaccounts")
        return [item.get("adaccount", item) for item in data.get("adaccounts", [])]

    def get_ad_account(self, ad_account_id: str) -> dict:
        """Get an ad account by ID.

        Args:
            ad_account_id: Ad account ID.

        Returns:
            Ad account dict.
        """
        data = self._get(f"/adaccounts/{ad_account_id}")
        items = data.get("adaccounts", [])
        return items[0].get("adaccount", items[0]) if items else {}

    # -- Campaigns ---------------------------------------------------------

    def list_campaigns(self, ad_account_id: str | None = None) -> list[dict]:
        """List campaigns in an ad account.

        Args:
            ad_account_id: Ad account ID (uses default if not provided).

        Returns:
            List of campaign dicts.
        """
        acct = ad_account_id or self.ad_account_id
        data = self._get(f"/adaccounts/{acct}/campaigns")
        return [item.get("campaign", item) for item in data.get("campaigns", [])]

    def create_campaign(
        self,
        name: str,
        status: str = "PAUSED",
        objective: str = "AWARENESS",
        ad_account_id: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a campaign.

        Args:
            name:           Campaign name.
            status:         "ACTIVE" or "PAUSED".
            objective:      Campaign objective (AWARENESS, CONSIDERATION, CONVERSIONS, etc.).
            ad_account_id:  Ad account ID (uses default if not provided).
            kwargs:         Additional fields (start_time, end_time, daily_budget_micro, etc.).

        Returns:
            Created campaign dict.
        """
        acct = ad_account_id or self.ad_account_id
        campaign = {"name": name, "status": status, "objective": objective, **kwargs}
        data = self._post(
            f"/adaccounts/{acct}/campaigns",
            json={"campaigns": [{"campaign": campaign}]},
        )
        items = data.get("campaigns", [])
        return items[0].get("campaign", items[0]) if items else {}

    def get_campaign_stats(
        self,
        campaign_id: str,
        granularity: str = "TOTAL",
        fields: str = "impressions,spend,swipes",
    ) -> list[dict]:
        """Get campaign performance statistics.

        Args:
            campaign_id: Campaign ID.
            granularity: "TOTAL", "DAY", or "HOUR".
            fields:      Comma-separated stat fields.

        Returns:
            List of stats dicts.
        """
        params = {"granularity": granularity, "fields": fields}
        data = self._get(f"/campaigns/{campaign_id}/stats", params=params)
        return data.get("timeseries_stats", data.get("total_stats", []))

    # -- Ad Squads (Ad Sets) -----------------------------------------------

    def list_ad_squads(self, campaign_id: str) -> list[dict]:
        """List ad squads in a campaign.

        Args:
            campaign_id: Campaign ID.

        Returns:
            List of ad squad dicts.
        """
        data = self._get(f"/campaigns/{campaign_id}/adsquads")
        return [item.get("adsquad", item) for item in data.get("adsquads", [])]

    # -- Media / Creatives -------------------------------------------------

    def create_media(
        self,
        name: str,
        type: str = "VIDEO",
        ad_account_id: str | None = None,
    ) -> dict:
        """Create a media entity for creative uploads.

        Args:
            name:          Media name.
            type:          "VIDEO" or "IMAGE".
            ad_account_id: Ad account ID (uses default if not provided).

        Returns:
            Created media dict with upload URL.
        """
        acct = ad_account_id or self.ad_account_id
        data = self._post(
            f"/adaccounts/{acct}/media",
            json={"media": [{"media": {"name": name, "type": type}}]},
        )
        items = data.get("media", [])
        return items[0].get("media", items[0]) if items else {}

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("request_status") and body or body

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
