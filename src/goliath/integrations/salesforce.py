"""
Salesforce Integration — manage contacts, accounts, and opportunities via the Salesforce REST API.

SETUP INSTRUCTIONS
==================

1. Log in to Salesforce and go to Setup.

2. Create a Connected App:
   - Setup > App Manager > New Connected App.
   - Enable OAuth Settings.
   - Callback URL: https://login.salesforce.com/services/oauth2/callback
   - Scopes: Full access (full), or specific: api, refresh_token

3. For server-to-server automation, use the Username-Password OAuth flow:
   - You'll need your Security Token (Settings > Reset Security Token).
   - Password = your_password + security_token (concatenated).

4. Add to your .env:
     SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
     SALESFORCE_ACCESS_TOKEN=your-access-token

   OR for username-password flow:
     SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
     SALESFORCE_CLIENT_ID=your-connected-app-client-id
     SALESFORCE_CLIENT_SECRET=your-connected-app-secret
     SALESFORCE_USERNAME=your-username
     SALESFORCE_PASSWORD=your-password-plus-security-token

IMPORTANT NOTES
===============
- Instance URL varies by org (e.g. https://na1.salesforce.com).
- API version is pinned to v59.0. Update _API_VERSION for newer versions.
- Rate limits depend on your Salesforce edition (typically 15,000–100,000/day).
- SOQL queries are used for searching records.

Usage:
    from goliath.integrations.salesforce import SalesforceClient

    sf = SalesforceClient()

    # Query contacts
    contacts = sf.query("SELECT Id, Name, Email FROM Contact LIMIT 10")

    # Create a contact
    sf.create("Contact", {"FirstName": "Jane", "LastName": "Doe", "Email": "jane@example.com"})

    # Update a record
    sf.update("Contact", "003xxx", {"Phone": "+15551234567"})

    # Get a record
    record = sf.get("Account", "001xxx")
"""

import requests

from goliath import config

_API_VERSION = "v59.0"
_TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"


class SalesforceClient:
    """Salesforce REST API client for CRM operations."""

    def __init__(self):
        has_token = bool(config.SALESFORCE_ACCESS_TOKEN)
        has_password_flow = (
            config.SALESFORCE_CLIENT_ID
            and config.SALESFORCE_CLIENT_SECRET
            and config.SALESFORCE_USERNAME
            and config.SALESFORCE_PASSWORD
        )

        if not config.SALESFORCE_INSTANCE_URL:
            raise RuntimeError(
                "SALESFORCE_INSTANCE_URL is not set "
                "(e.g. 'https://your-instance.salesforce.com'). "
                "Add it to .env or export as an environment variable."
            )

        if not has_token and not has_password_flow:
            raise RuntimeError(
                "Salesforce credentials not set. Provide SALESFORCE_ACCESS_TOKEN "
                "or all of SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, "
                "SALESFORCE_USERNAME, SALESFORCE_PASSWORD. "
                "See integrations/salesforce.py for setup instructions."
            )

        self._instance = config.SALESFORCE_INSTANCE_URL.rstrip("/")
        self._base = f"{self._instance}/services/data/{_API_VERSION}"
        self.session = requests.Session()

        if has_token:
            self.session.headers["Authorization"] = (
                f"Bearer {config.SALESFORCE_ACCESS_TOKEN}"
            )
        else:
            self._authenticate_password_flow()

    def _authenticate_password_flow(self):
        """Authenticate via Username-Password OAuth flow."""
        resp = requests.post(
            _TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": config.SALESFORCE_CLIENT_ID,
                "client_secret": config.SALESFORCE_CLIENT_SECRET,
                "username": config.SALESFORCE_USERNAME,
                "password": config.SALESFORCE_PASSWORD,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(
                f"Salesforce auth failed: {data.get('error', 'unknown')} — "
                f"{data.get('error_description', 'no details')}"
            )

        self.session.headers["Authorization"] = f"Bearer {data['access_token']}"

    # -- Generic CRUD ------------------------------------------------------

    def query(self, soql: str) -> list[dict]:
        """Execute a SOQL query.

        Args:
            soql: SOQL query string.

        Returns:
            List of record dicts.
        """
        return self._get("/query", params={"q": soql}).get("records", [])

    def get(
        self, sobject: str, record_id: str, fields: list[str] | None = None
    ) -> dict:
        """Get a record by ID.

        Args:
            sobject:   SObject type (e.g. "Contact", "Account", "Opportunity").
            record_id: Salesforce record ID.
            fields:    Optional list of field names to return.

        Returns:
            Record dict.
        """
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._get(f"/sobjects/{sobject}/{record_id}", params=params)

    def create(self, sobject: str, data: dict) -> dict:
        """Create a new record.

        Args:
            sobject: SObject type.
            data:    Field values dict.

        Returns:
            Dict with id, success, and errors.
        """
        return self._post(f"/sobjects/{sobject}", json=data)

    def update(self, sobject: str, record_id: str, data: dict) -> None:
        """Update a record.

        Args:
            sobject:   SObject type.
            record_id: Salesforce record ID.
            data:      Fields to update.
        """
        resp = self.session.patch(
            f"{self._base}/sobjects/{sobject}/{record_id}", json=data
        )
        resp.raise_for_status()

    def delete(self, sobject: str, record_id: str) -> None:
        """Delete a record.

        Args:
            sobject:   SObject type.
            record_id: Salesforce record ID.
        """
        resp = self.session.delete(f"{self._base}/sobjects/{sobject}/{record_id}")
        resp.raise_for_status()

    # -- Convenience methods -----------------------------------------------

    def list_sobjects(self) -> list[dict]:
        """List all available SObject types.

        Returns:
            List of SObject describe dicts.
        """
        return self._get("/sobjects").get("sobjects", [])

    def describe(self, sobject: str) -> dict:
        """Describe an SObject's metadata and fields.

        Args:
            sobject: SObject type name.

        Returns:
            SObject describe dict.
        """
        return self._get(f"/sobjects/{sobject}/describe")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
