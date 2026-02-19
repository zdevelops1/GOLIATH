"""
HubSpot Integration — manage contacts, deals, and companies via the HubSpot API v3.

SETUP INSTRUCTIONS
==================

1. Log in to HubSpot at https://app.hubspot.com

2. Go to Settings > Integrations > Private Apps.

3. Click "Create a private app".
   - Name: "GOLIATH"
   - Scopes: crm.objects.contacts.read, crm.objects.contacts.write,
     crm.objects.deals.read, crm.objects.deals.write,
     crm.objects.companies.read, crm.objects.companies.write

4. Copy the access token.

5. Add to your .env:
     HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx

IMPORTANT NOTES
===============
- Private app tokens don't expire but can be revoked.
- Rate limit: 100 requests per 10 seconds (private apps).
- All CRM objects use the same CRUD pattern.
- Properties are key-value pairs (e.g. {"email": "user@example.com"}).
- Search supports filtering, sorting, and pagination.

Usage:
    from goliath.integrations.hubspot import HubSpotClient

    hs = HubSpotClient()

    # Create a contact
    hs.create_contact(properties={"email": "jane@example.com", "firstname": "Jane"})

    # Search contacts
    results = hs.search_contacts(query="jane@example.com")

    # Create a deal
    hs.create_deal(properties={"dealname": "New Deal", "amount": "5000", "pipeline": "default"})

    # List companies
    companies = hs.list_companies(limit=10)
"""

import requests

from goliath import config

_API_BASE = "https://api.hubapi.com/crm/v3"


class HubSpotClient:
    """HubSpot CRM API v3 client for contacts, deals, and companies."""

    def __init__(self):
        if not config.HUBSPOT_ACCESS_TOKEN:
            raise RuntimeError(
                "HUBSPOT_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/hubspot.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.HUBSPOT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- Contacts ----------------------------------------------------------

    def create_contact(self, properties: dict) -> dict:
        """Create a contact.

        Args:
            properties: Contact properties (e.g. {"email": "...", "firstname": "..."}).

        Returns:
            Created contact resource dict.
        """
        return self._post("/objects/contacts", json={"properties": properties})

    def get_contact(self, contact_id: str, properties: list[str] | None = None) -> dict:
        """Get a contact by ID.

        Args:
            contact_id: HubSpot contact ID.
            properties: Optional list of property names to include.

        Returns:
            Contact resource dict.
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)
        return self._get(f"/objects/contacts/{contact_id}", params=params)

    def update_contact(self, contact_id: str, properties: dict) -> dict:
        """Update a contact.

        Args:
            contact_id: HubSpot contact ID.
            properties: Properties to update.

        Returns:
            Updated contact resource dict.
        """
        return self._patch(
            f"/objects/contacts/{contact_id}", json={"properties": properties}
        )

    def list_contacts(
        self, limit: int = 10, properties: list[str] | None = None
    ) -> list[dict]:
        """List contacts.

        Args:
            limit:      Number of results (1–100).
            properties: Optional property names to include.

        Returns:
            List of contact resource dicts.
        """
        params: dict = {"limit": limit}
        if properties:
            params["properties"] = ",".join(properties)
        return self._get("/objects/contacts", params=params).get("results", [])

    def search_contacts(self, query: str, limit: int = 10) -> list[dict]:
        """Search contacts by query string.

        Args:
            query: Search query (matches name, email, phone, etc.).
            limit: Number of results.

        Returns:
            List of matching contact dicts.
        """
        body = {
            "query": query,
            "limit": limit,
        }
        return self._post("/objects/contacts/search", json=body).get("results", [])

    def delete_contact(self, contact_id: str) -> None:
        """Delete a contact.

        Args:
            contact_id: HubSpot contact ID.
        """
        resp = self.session.delete(f"{_API_BASE}/objects/contacts/{contact_id}")
        resp.raise_for_status()

    # -- Deals -------------------------------------------------------------

    def create_deal(self, properties: dict) -> dict:
        """Create a deal.

        Args:
            properties: Deal properties (e.g. {"dealname": "...", "amount": "..."}).

        Returns:
            Created deal resource dict.
        """
        return self._post("/objects/deals", json={"properties": properties})

    def get_deal(self, deal_id: str) -> dict:
        """Get a deal by ID.

        Args:
            deal_id: HubSpot deal ID.

        Returns:
            Deal resource dict.
        """
        return self._get(f"/objects/deals/{deal_id}")

    def update_deal(self, deal_id: str, properties: dict) -> dict:
        """Update a deal.

        Args:
            deal_id:    HubSpot deal ID.
            properties: Properties to update.

        Returns:
            Updated deal resource dict.
        """
        return self._patch(f"/objects/deals/{deal_id}", json={"properties": properties})

    def list_deals(self, limit: int = 10) -> list[dict]:
        """List deals.

        Args:
            limit: Number of results (1–100).

        Returns:
            List of deal resource dicts.
        """
        return self._get("/objects/deals", params={"limit": limit}).get("results", [])

    # -- Companies ---------------------------------------------------------

    def create_company(self, properties: dict) -> dict:
        """Create a company.

        Args:
            properties: Company properties (e.g. {"name": "...", "domain": "..."}).

        Returns:
            Created company resource dict.
        """
        return self._post("/objects/companies", json={"properties": properties})

    def get_company(self, company_id: str) -> dict:
        """Get a company by ID.

        Args:
            company_id: HubSpot company ID.

        Returns:
            Company resource dict.
        """
        return self._get(f"/objects/companies/{company_id}")

    def list_companies(self, limit: int = 10) -> list[dict]:
        """List companies.

        Args:
            limit: Number of results (1–100).

        Returns:
            List of company resource dicts.
        """
        return self._get("/objects/companies", params={"limit": limit}).get(
            "results", []
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, **kwargs) -> dict:
        resp = self.session.patch(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
