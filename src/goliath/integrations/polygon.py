"""
Polygon.io Integration — real-time and historical stock, options, forex, and crypto data.

SETUP INSTRUCTIONS
==================

1. Go to https://polygon.io/ and create an account.

2. Your API key is on the dashboard (https://polygon.io/dashboard/api-keys).

3. Copy the key and add to your .env:
     POLYGON_API_KEY=your-api-key

IMPORTANT NOTES
===============
- API docs: https://polygon.io/docs/stocks
- Free tier: 5 API calls/minute, end-of-day data.
- Starter/Developer plans: real-time data, higher limits.
- Base URL: https://api.polygon.io
- Authentication: apiKey query parameter.

Usage:
    from goliath.integrations.polygon import PolygonClient

    pg = PolygonClient()

    # Get previous day's OHLC
    prev = pg.get_previous_close("AAPL")

    # Get aggregates (bars)
    bars = pg.get_aggregates("AAPL", multiplier=1, timespan="day",
                             from_date="2025-01-01", to_date="2025-01-31")

    # Get ticker details
    details = pg.get_ticker_details("AAPL")

    # Search tickers
    results = pg.search_tickers("Tesla")

    # Get last trade
    trade = pg.get_last_trade("AAPL")

    # Get last quote (NBBO)
    quote = pg.get_last_quote("AAPL")

    # Get market status
    status = pg.get_market_status()

    # Get grouped daily bars
    grouped = pg.get_grouped_daily("2025-01-15")

    # Get stock splits
    splits = pg.get_stock_splits("AAPL")

    # Get dividends
    dividends = pg.get_dividends("AAPL")
"""

import requests

from goliath import config

_API_BASE = "https://api.polygon.io"


class PolygonClient:
    """Polygon.io REST API client for stocks, options, forex, and crypto."""

    def __init__(self):
        if not config.POLYGON_API_KEY:
            raise RuntimeError(
                "POLYGON_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/polygon.py for setup instructions."
            )

        self.api_key = config.POLYGON_API_KEY
        self.session = requests.Session()

    # -- Aggregates (Bars) -----------------------------------------------------

    def get_aggregates(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "day",
        from_date: str = "",
        to_date: str = "",
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 5000,
    ) -> dict:
        """Get aggregate bars (OHLCV) for a ticker.

        Args:
            ticker:     Stock ticker (e.g. "AAPL").
            multiplier: Size of the timespan multiplier.
            timespan:   "minute", "hour", "day", "week", "month", "quarter", "year".
            from_date:  Start date (YYYY-MM-DD).
            to_date:    End date (YYYY-MM-DD).
            adjusted:   Whether results are adjusted for splits.
            sort:       "asc" or "desc".
            limit:      Max results (max 50000).

        Returns:
            Dict with "results" list of bar dicts.
        """
        return self._get(
            f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}"
            f"/{from_date}/{to_date}",
            params={"adjusted": str(adjusted).lower(), "sort": sort, "limit": limit},
        )

    def get_previous_close(self, ticker: str, adjusted: bool = True) -> dict:
        """Get previous day's OHLCV.

        Args:
            ticker:   Stock ticker.
            adjusted: Whether results are adjusted for splits.

        Returns:
            Dict with "results" list.
        """
        return self._get(
            f"/v2/aggs/ticker/{ticker}/prev",
            params={"adjusted": str(adjusted).lower()},
        )

    def get_grouped_daily(self, date: str, adjusted: bool = True) -> dict:
        """Get grouped daily bars for all tickers on a given date.

        Args:
            date:     Date (YYYY-MM-DD).
            adjusted: Adjusted for splits.

        Returns:
            Dict with "results" list of bar dicts.
        """
        return self._get(
            f"/v2/aggs/grouped/locale/us/market/stocks/{date}",
            params={"adjusted": str(adjusted).lower()},
        )

    # -- Ticker Info -----------------------------------------------------------

    def get_ticker_details(self, ticker: str) -> dict:
        """Get detailed info for a ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            Ticker details dict.
        """
        data = self._get(f"/v3/reference/tickers/{ticker}")
        return data.get("results", data)

    def search_tickers(
        self,
        search: str = "",
        ticker_type: str | None = None,
        market: str | None = None,
        active: bool = True,
        limit: int = 100,
    ) -> list[dict]:
        """Search for tickers.

        Args:
            search:      Search query.
            ticker_type: Filter by type ("CS" common stock, "ETF", etc.).
            market:      Filter by market ("stocks", "crypto", "fx", "otc").
            active:      Only active tickers.
            limit:       Max results.

        Returns:
            List of ticker dicts.
        """
        params: dict = {"search": search, "active": str(active).lower(), "limit": limit}
        if ticker_type:
            params["type"] = ticker_type
        if market:
            params["market"] = market
        data = self._get("/v3/reference/tickers", params=params)
        return data.get("results", [])

    # -- Trades & Quotes -------------------------------------------------------

    def get_last_trade(self, ticker: str) -> dict:
        """Get the last trade for a ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            Last trade dict.
        """
        data = self._get(f"/v2/last/trade/{ticker}")
        return data.get("results", data)

    def get_last_quote(self, ticker: str) -> dict:
        """Get the last NBBO quote for a ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            Last quote dict.
        """
        data = self._get(f"/v2/last/nbbo/{ticker}")
        return data.get("results", data)

    # -- Reference Data --------------------------------------------------------

    def get_stock_splits(self, ticker: str) -> list[dict]:
        """Get stock splits for a ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            List of split dicts.
        """
        data = self._get(
            "/v3/reference/splits", params={"ticker": ticker}
        )
        return data.get("results", [])

    def get_dividends(self, ticker: str) -> list[dict]:
        """Get dividends for a ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            List of dividend dicts.
        """
        data = self._get(
            "/v3/reference/dividends", params={"ticker": ticker}
        )
        return data.get("results", [])

    def get_market_holidays(self) -> list[dict]:
        """Get upcoming market holidays and their status.

        Returns:
            List of holiday dicts.
        """
        return self._get("/v1/marketstatus/upcoming")

    def get_market_status(self) -> dict:
        """Get current market status.

        Returns:
            Market status dict.
        """
        return self._get("/v1/marketstatus/now")

    # -- Crypto ----------------------------------------------------------------

    def get_crypto_previous_close(self, ticker: str) -> dict:
        """Get previous day's crypto OHLCV (e.g. "X:BTCUSD").

        Args:
            ticker: Crypto pair (e.g. "X:BTCUSD").

        Returns:
            Dict with "results" list.
        """
        return self._get(f"/v2/aggs/ticker/{ticker}/prev")

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        params = kwargs.pop("params", {})
        params["apiKey"] = self.api_key
        resp = self.session.get(f"{_API_BASE}{path}", params=params, **kwargs)
        resp.raise_for_status()
        return resp.json()
