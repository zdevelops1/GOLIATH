"""
Plaid Integration — access bank accounts, transactions, and balances via the Plaid API.

SETUP INSTRUCTIONS
==================

1. Sign up at https://dashboard.plaid.com/signup

2. Go to Team Settings > Keys (https://dashboard.plaid.com/team/keys).

3. Copy your client_id and secret (sandbox or development).

4. Add to your .env:
     PLAID_CLIENT_ID=your-client-id
     PLAID_SECRET=your-secret
     PLAID_ENV=sandbox

   Environments: "sandbox", "development", "production".

IMPORTANT NOTES
===============
- API docs: https://plaid.com/docs/api/
- Sandbox for testing: use test credentials from https://plaid.com/docs/sandbox/
- Base URLs:
  - Sandbox: https://sandbox.plaid.com
  - Development: https://development.plaid.com
  - Production: https://production.plaid.com
- Most endpoints require an access_token obtained via Link.

Usage:
    from goliath.integrations.plaid import PlaidClient

    plaid = PlaidClient()

    # Create a link token (for initializing Plaid Link)
    link = plaid.create_link_token(
        user_id="user-123",
        products=["transactions"],
        country_codes=["US"],
    )

    # Exchange a public token for an access token
    access = plaid.exchange_public_token("public-sandbox-xxxx")

    # Get account balances
    balances = plaid.get_balance(access_token="access-sandbox-xxxx")

    # Get transactions
    txns = plaid.get_transactions(
        access_token="access-sandbox-xxxx",
        start_date="2025-01-01",
        end_date="2025-01-31",
    )

    # Get account info
    accounts = plaid.get_accounts(access_token="access-sandbox-xxxx")

    # Get institution details
    inst = plaid.get_institution("ins_3")
"""

import requests

from goliath import config

_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidClient:
    """Plaid API client for banking data, transactions, and balances."""

    def __init__(self):
        if not config.PLAID_CLIENT_ID or not config.PLAID_SECRET:
            raise RuntimeError(
                "PLAID_CLIENT_ID and PLAID_SECRET must both be set. "
                "Add them to .env or export as environment variables. "
                "See integrations/plaid.py for setup instructions."
            )

        self.client_id = config.PLAID_CLIENT_ID
        self.secret = config.PLAID_SECRET

        env = getattr(config, "PLAID_ENV", "") or "sandbox"
        self.base_url = _ENV_URLS.get(env, _ENV_URLS["sandbox"])

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Link ------------------------------------------------------------------

    def create_link_token(
        self,
        user_id: str,
        products: list[str] | None = None,
        country_codes: list[str] | None = None,
        language: str = "en",
    ) -> dict:
        """Create a Link token for initializing Plaid Link.

        Args:
            user_id:       Unique user ID.
            products:      Plaid products (["transactions", "auth", "identity"]).
            country_codes: Country codes (["US", "CA"]).
            language:      Language code.

        Returns:
            Link token dict with "link_token" and "expiration".
        """
        payload: dict = {
            **self._auth(),
            "user": {"client_user_id": user_id},
            "client_name": "GOLIATH",
            "products": products or ["transactions"],
            "country_codes": country_codes or ["US"],
            "language": language,
        }
        return self._post("/link/token/create", json=payload)

    def exchange_public_token(self, public_token: str) -> dict:
        """Exchange a public token for an access token.

        Args:
            public_token: Public token from Plaid Link.

        Returns:
            Dict with "access_token" and "item_id".
        """
        return self._post(
            "/item/public_token/exchange",
            json={**self._auth(), "public_token": public_token},
        )

    # -- Accounts & Balances ---------------------------------------------------

    def get_accounts(self, access_token: str) -> list[dict]:
        """Get account information.

        Args:
            access_token: Plaid access token.

        Returns:
            List of account dicts.
        """
        data = self._post(
            "/accounts/get",
            json={**self._auth(), "access_token": access_token},
        )
        return data.get("accounts", [])

    def get_balance(self, access_token: str) -> list[dict]:
        """Get real-time account balances.

        Args:
            access_token: Plaid access token.

        Returns:
            List of account dicts with balance info.
        """
        data = self._post(
            "/accounts/balance/get",
            json={**self._auth(), "access_token": access_token},
        )
        return data.get("accounts", [])

    # -- Transactions ----------------------------------------------------------

    def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str,
        count: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get transactions for a date range.

        Args:
            access_token: Plaid access token.
            start_date:   Start date (YYYY-MM-DD).
            end_date:     End date (YYYY-MM-DD).
            count:        Max results per page.
            offset:       Pagination offset.

        Returns:
            Dict with "transactions", "accounts", and "total_transactions".
        """
        return self._post(
            "/transactions/get",
            json={
                **self._auth(),
                "access_token": access_token,
                "start_date": start_date,
                "end_date": end_date,
                "options": {"count": count, "offset": offset},
            },
        )

    # -- Identity --------------------------------------------------------------

    def get_identity(self, access_token: str) -> list[dict]:
        """Get identity information (name, address, etc.) for accounts.

        Args:
            access_token: Plaid access token.

        Returns:
            List of account dicts with identity info.
        """
        data = self._post(
            "/identity/get",
            json={**self._auth(), "access_token": access_token},
        )
        return data.get("accounts", [])

    # -- Institutions ----------------------------------------------------------

    def get_institution(
        self,
        institution_id: str,
        country_codes: list[str] | None = None,
    ) -> dict:
        """Get institution details.

        Args:
            institution_id: Institution ID (e.g. "ins_3").
            country_codes:  Country codes.

        Returns:
            Institution dict.
        """
        data = self._post(
            "/institutions/get_by_id",
            json={
                **self._auth(),
                "institution_id": institution_id,
                "country_codes": country_codes or ["US"],
            },
        )
        return data.get("institution", {})

    def search_institutions(
        self,
        query: str,
        products: list[str] | None = None,
        country_codes: list[str] | None = None,
    ) -> list[dict]:
        """Search institutions by name.

        Args:
            query:         Search query.
            products:      Filter by supported products.
            country_codes: Country codes.

        Returns:
            List of institution dicts.
        """
        data = self._post(
            "/institutions/search",
            json={
                **self._auth(),
                "query": query,
                "products": products or ["transactions"],
                "country_codes": country_codes or ["US"],
            },
        )
        return data.get("institutions", [])

    # -- internal helpers ------------------------------------------------------

    def _auth(self) -> dict:
        return {"client_id": self.client_id, "secret": self.secret}

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
