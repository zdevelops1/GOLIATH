"""
CoinGecko Integration — crypto prices, market data, exchanges, and trending coins.

SETUP INSTRUCTIONS
==================

1. CoinGecko has a free public API (no key required for basic endpoints).

2. For higher rate limits, sign up for CoinGecko Pro at https://www.coingecko.com/en/api/pricing
   and get a Demo or Pro API key.

3. Add to your .env (optional — free tier works without):
     COINGECKO_API_KEY=your-api-key

   For Pro API:
     COINGECKO_API_KEY=your-pro-key
     COINGECKO_PRO=true

IMPORTANT NOTES
===============
- Free API docs: https://docs.coingecko.com/reference/introduction
- Free tier: 10-30 calls/minute (no key needed).
- Demo API: 30 calls/minute with key.
- Pro API: 500 calls/minute.
- Free base URL: https://api.coingecko.com/api/v3
- Pro base URL: https://pro-api.coingecko.com/api/v3

Usage:
    from goliath.integrations.coingecko import CoinGeckoClient

    cg = CoinGeckoClient()

    # Get Bitcoin price in USD
    price = cg.get_price("bitcoin", vs_currencies="usd")

    # Get top coins by market cap
    markets = cg.get_markets(vs_currency="usd", per_page=10)

    # Get coin details
    coin = cg.get_coin("ethereum")

    # Get coin market chart (historical prices)
    chart = cg.get_market_chart("bitcoin", vs_currency="usd", days=30)

    # Get trending coins
    trending = cg.get_trending()

    # Search for coins
    results = cg.search("solana")

    # Get exchange list
    exchanges = cg.get_exchanges()

    # Get global crypto stats
    global_data = cg.get_global()

    # Get list of supported vs currencies
    currencies = cg.get_supported_vs_currencies()

    # Get coin OHLC
    ohlc = cg.get_ohlc("bitcoin", vs_currency="usd", days=14)
"""

import requests

from goliath import config

_FREE_BASE = "https://api.coingecko.com/api/v3"
_PRO_BASE = "https://pro-api.coingecko.com/api/v3"


class CoinGeckoClient:
    """CoinGecko API client for crypto prices, market data, and trends."""

    def __init__(self):
        self.api_key = getattr(config, "COINGECKO_API_KEY", "") or ""
        is_pro = (
            getattr(config, "COINGECKO_PRO", "") or ""
        ).lower() in ("true", "1", "yes")

        self.base_url = _PRO_BASE if (is_pro and self.api_key) else _FREE_BASE

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.api_key:
            if is_pro:
                self.session.headers["x-cg-pro-api-key"] = self.api_key
            else:
                self.session.headers["x-cg-demo-api-key"] = self.api_key

    # -- Simple Price ----------------------------------------------------------

    def get_price(
        self,
        ids: str,
        vs_currencies: str = "usd",
        include_24hr_change: bool = False,
        include_market_cap: bool = False,
    ) -> dict:
        """Get current price for one or more coins.

        Args:
            ids:                 Comma-separated coin IDs (e.g. "bitcoin,ethereum").
            vs_currencies:       Comma-separated target currencies (e.g. "usd,eur").
            include_24hr_change: Include 24h price change percentage.
            include_market_cap:  Include market cap.

        Returns:
            Dict keyed by coin ID with price data.
        """
        params: dict = {
            "ids": ids,
            "vs_currencies": vs_currencies,
            "include_24hr_change": str(include_24hr_change).lower(),
            "include_market_cap": str(include_market_cap).lower(),
        }
        return self._get("/simple/price", params=params)

    def get_supported_vs_currencies(self) -> list[str]:
        """Get list of supported target currencies.

        Returns:
            List of currency strings (e.g. ["usd", "eur", "btc"]).
        """
        return self._get("/simple/supported_vs_currencies")

    # -- Coins -----------------------------------------------------------------

    def get_markets(
        self,
        vs_currency: str = "usd",
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        category: str | None = None,
    ) -> list[dict]:
        """Get coin market data (price, market cap, volume).

        Args:
            vs_currency: Target currency.
            order:       Sort order ("market_cap_desc","volume_desc","id_asc", etc.).
            per_page:    Results per page (max 250).
            page:        Page number.
            category:    Filter by category (e.g. "decentralized-finance-defi").

        Returns:
            List of coin market dicts.
        """
        params: dict = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
        }
        if category:
            params["category"] = category
        return self._get("/coins/markets", params=params)

    def get_coin(self, coin_id: str) -> dict:
        """Get detailed coin data.

        Args:
            coin_id: Coin ID (e.g. "bitcoin", "ethereum").

        Returns:
            Detailed coin dict.
        """
        return self._get(
            f"/coins/{coin_id}",
            params={"localization": "false", "tickers": "false"},
        )

    def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
        interval: str | None = None,
    ) -> dict:
        """Get historical market data (price, market cap, volume).

        Args:
            coin_id:     Coin ID.
            vs_currency: Target currency.
            days:        Number of days (1, 7, 14, 30, 90, 180, 365, "max").
            interval:    Data interval ("daily" for days > 1, auto otherwise).

        Returns:
            Dict with "prices", "market_caps", "total_volumes" arrays.
        """
        params: dict = {"vs_currency": vs_currency, "days": days}
        if interval:
            params["interval"] = interval
        return self._get(f"/coins/{coin_id}/market_chart", params=params)

    def get_ohlc(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 14,
    ) -> list[list]:
        """Get coin OHLC data.

        Args:
            coin_id:     Coin ID.
            vs_currency: Target currency.
            days:        Number of days (1, 7, 14, 30, 90, 180, 365).

        Returns:
            List of [timestamp, open, high, low, close] arrays.
        """
        return self._get(
            f"/coins/{coin_id}/ohlc",
            params={"vs_currency": vs_currency, "days": days},
        )

    # -- Search & Trending -----------------------------------------------------

    def search(self, query: str) -> dict:
        """Search for coins, exchanges, and categories.

        Args:
            query: Search string.

        Returns:
            Dict with "coins", "exchanges", "categories" lists.
        """
        return self._get("/search", params={"query": query})

    def get_trending(self) -> dict:
        """Get trending coins (top-7 by search popularity).

        Returns:
            Dict with "coins" list of trending items.
        """
        return self._get("/search/trending")

    # -- Exchanges -------------------------------------------------------------

    def get_exchanges(self, per_page: int = 100, page: int = 1) -> list[dict]:
        """List exchanges by trading volume.

        Args:
            per_page: Results per page (max 250).
            page:     Page number.

        Returns:
            List of exchange dicts.
        """
        return self._get(
            "/exchanges", params={"per_page": per_page, "page": page}
        )

    def get_exchange(self, exchange_id: str) -> dict:
        """Get exchange details.

        Args:
            exchange_id: Exchange ID (e.g. "binance", "coinbase-exchange").

        Returns:
            Exchange details dict.
        """
        return self._get(f"/exchanges/{exchange_id}")

    # -- Global ----------------------------------------------------------------

    def get_global(self) -> dict:
        """Get global cryptocurrency stats.

        Returns:
            Dict with total market cap, volume, dominance, etc.
        """
        data = self._get("/global")
        return data.get("data", data)

    # -- Categories ------------------------------------------------------------

    def get_categories(self) -> list[dict]:
        """List coin categories with market data.

        Returns:
            List of category dicts.
        """
        return self._get("/coins/categories")

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
