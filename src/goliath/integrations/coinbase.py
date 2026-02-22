"""
Coinbase Integration — market data, accounts, and transactions via the Coinbase API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.coinbase.com/ and create an account.

2. Navigate to Settings > API (https://www.coinbase.com/settings/api).

3. Click "New API Key", select the permissions you need, and confirm.

4. Copy the API Key and API Secret and add to your .env:
     COINBASE_API_KEY=your-api-key
     COINBASE_API_SECRET=your-api-secret

IMPORTANT NOTES
===============
- Coinbase Advanced Trade API: https://docs.cdp.coinbase.com/advanced-trade/docs/welcome
- Public endpoints (prices, products) do NOT require authentication.
- Authenticated endpoints (accounts, orders) require API key + secret.
- Rate limits: 10 requests/second per API key.
- Base URL: https://api.coinbase.com

Usage:
    from goliath.integrations.coinbase import CoinbaseClient

    cb = CoinbaseClient()

    # Get spot price for BTC in USD
    price = cb.get_spot_price("BTC-USD")

    # Get buy/sell prices
    buy = cb.get_buy_price("BTC-USD")
    sell = cb.get_sell_price("BTC-USD")

    # List exchange rates
    rates = cb.get_exchange_rates(currency="USD")

    # List supported currencies
    currencies = cb.list_currencies()

    # Get server time
    server_time = cb.get_time()

    # List accounts (requires auth)
    accounts = cb.list_accounts()

    # Get account details (requires auth)
    account = cb.get_account("account-id")

    # List transactions for an account (requires auth)
    txns = cb.list_transactions("account-id")
"""

import hashlib
import hmac
import time

import requests

from goliath import config

_API_BASE = "https://api.coinbase.com"


class CoinbaseClient:
    """Coinbase API client for market data, accounts, and transactions."""

    def __init__(self):
        self.api_key = getattr(config, "COINBASE_API_KEY", "") or ""
        self.api_secret = getattr(config, "COINBASE_API_SECRET", "") or ""

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Market Data (Public) --------------------------------------------------

    def get_spot_price(self, currency_pair: str) -> dict:
        """Get current spot price.

        Args:
            currency_pair: Trading pair (e.g. "BTC-USD", "ETH-EUR").

        Returns:
            Dict with "amount" and "currency".
        """
        data = self._public_get(f"/v2/prices/{currency_pair}/spot")
        return data.get("data", data)

    def get_buy_price(self, currency_pair: str) -> dict:
        """Get buy price (includes Coinbase fee).

        Args:
            currency_pair: Trading pair (e.g. "BTC-USD").

        Returns:
            Dict with "amount" and "currency".
        """
        data = self._public_get(f"/v2/prices/{currency_pair}/buy")
        return data.get("data", data)

    def get_sell_price(self, currency_pair: str) -> dict:
        """Get sell price.

        Args:
            currency_pair: Trading pair (e.g. "BTC-USD").

        Returns:
            Dict with "amount" and "currency".
        """
        data = self._public_get(f"/v2/prices/{currency_pair}/sell")
        return data.get("data", data)

    def get_exchange_rates(self, currency: str = "USD") -> dict:
        """Get exchange rates for a currency.

        Args:
            currency: Base currency (default "USD").

        Returns:
            Dict with "currency" and "rates" mapping.
        """
        data = self._public_get("/v2/exchange-rates", params={"currency": currency})
        return data.get("data", data)

    def list_currencies(self) -> list[dict]:
        """List supported currencies.

        Returns:
            List of currency dicts.
        """
        data = self._public_get("/v2/currencies")
        return data.get("data", [])

    def get_time(self) -> dict:
        """Get server time.

        Returns:
            Dict with "iso" and "epoch" timestamps.
        """
        data = self._public_get("/v2/time")
        return data.get("data", data)

    # -- Accounts (Authenticated) ----------------------------------------------

    def list_accounts(self) -> list[dict]:
        """List accounts (requires API key + secret).

        Returns:
            List of account dicts.
        """
        data = self._auth_get("/v2/accounts")
        return data.get("data", [])

    def get_account(self, account_id: str) -> dict:
        """Get account details.

        Args:
            account_id: Account UUID.

        Returns:
            Account dict.
        """
        data = self._auth_get(f"/v2/accounts/{account_id}")
        return data.get("data", data)

    # -- Transactions (Authenticated) ------------------------------------------

    def list_transactions(self, account_id: str) -> list[dict]:
        """List transactions for an account.

        Args:
            account_id: Account UUID.

        Returns:
            List of transaction dicts.
        """
        data = self._auth_get(f"/v2/accounts/{account_id}/transactions")
        return data.get("data", [])

    # -- internal helpers ------------------------------------------------------

    def _public_get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _auth_get(self, path: str) -> dict:
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "COINBASE_API_KEY and COINBASE_API_SECRET are required for "
                "authenticated endpoints. See integrations/coinbase.py for setup."
            )

        timestamp = str(int(time.time()))
        message = timestamp + "GET" + path
        signature = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-VERSION": "2024-01-01",
        }
        resp = self.session.get(f"{_API_BASE}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()
