"""
Yahoo Finance Integration — stock quotes, historical data, and company info via Yahoo Finance.

SETUP INSTRUCTIONS
==================

1. Go to https://financeapi.net/ (or https://rapidapi.com/sparior/api/yahoo-finance15)
   and sign up for a Yahoo Finance API key.

2. Copy your API key and add to your .env:
     YAHOO_FINANCE_API_KEY=your-api-key

   Alternatively, use the free YF endpoint (limited, may require headers).

IMPORTANT NOTES
===============
- This client uses the Yahoo Finance v8/v11 public quote endpoints.
- For higher reliability, use a RapidAPI-based Yahoo Finance provider.
- Rate limits depend on your provider.
- No official Yahoo Finance API exists; community endpoints may change.
- Base URL: https://query1.finance.yahoo.com (public) or custom via YAHOO_FINANCE_BASE_URL.

Usage:
    from goliath.integrations.yahoo_finance import YahooFinanceClient

    yf = YahooFinanceClient()

    # Get stock quote
    quote = yf.get_quote("AAPL")

    # Get multiple quotes
    quotes = yf.get_quotes(["AAPL", "MSFT", "GOOG"])

    # Get historical data (chart)
    chart = yf.get_chart("AAPL", interval="1d", range="1mo")

    # Get company profile / summary
    profile = yf.get_summary("AAPL")

    # Search for tickers
    results = yf.search("Tesla")

    # Get trending tickers
    trending = yf.get_trending()

    # Get market movers (gainers)
    gainers = yf.get_movers("gainers")
"""

import requests

from goliath import config

_DEFAULT_BASE = "https://query1.finance.yahoo.com"


class YahooFinanceClient:
    """Yahoo Finance API client for stock quotes, charts, and company data."""

    def __init__(self):
        api_key = getattr(config, "YAHOO_FINANCE_API_KEY", "") or ""
        self.base_url = (
            getattr(config, "YAHOO_FINANCE_BASE_URL", "") or _DEFAULT_BASE
        )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GOLIATH/1.0",
        })
        if api_key:
            self.session.headers["X-API-KEY"] = api_key

    # -- Quotes ----------------------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """Get real-time quote for a symbol.

        Args:
            symbol: Stock ticker (e.g. "AAPL", "MSFT").

        Returns:
            Quote dict with price, change, volume, etc.
        """
        data = self._get(
            "/v6/finance/quote", params={"symbols": symbol}
        )
        results = (
            data.get("quoteResponse", {}).get("result", [])
        )
        return results[0] if results else {}

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Get real-time quotes for multiple symbols.

        Args:
            symbols: List of stock tickers.

        Returns:
            List of quote dicts.
        """
        data = self._get(
            "/v6/finance/quote", params={"symbols": ",".join(symbols)}
        )
        return data.get("quoteResponse", {}).get("result", [])

    # -- Charts / Historical Data ----------------------------------------------

    def get_chart(
        self,
        symbol: str,
        interval: str = "1d",
        range: str = "1mo",
        period1: int | None = None,
        period2: int | None = None,
    ) -> dict:
        """Get historical OHLCV chart data.

        Args:
            symbol:   Stock ticker.
            interval: Data interval ("1m","2m","5m","15m","30m","60m","90m",
                      "1h","1d","5d","1wk","1mo","3mo").
            range:    Time range ("1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max").
            period1:  Start UNIX timestamp (overrides range).
            period2:  End UNIX timestamp.

        Returns:
            Chart data dict with timestamps and OHLCV arrays.
        """
        params: dict = {"interval": interval}
        if period1 is not None:
            params["period1"] = period1
            if period2 is not None:
                params["period2"] = period2
        else:
            params["range"] = range
        data = self._get(f"/v8/finance/chart/{symbol}", params=params)
        chart = data.get("chart", {})
        results = chart.get("result", [])
        return results[0] if results else {}

    # -- Company Info ----------------------------------------------------------

    def get_summary(self, symbol: str) -> dict:
        """Get company summary / profile.

        Args:
            symbol: Stock ticker.

        Returns:
            Summary dict with profile, financial data, etc.
        """
        return self._get(
            f"/v11/finance/quoteSummary/{symbol}",
            params={"modules": "assetProfile,summaryDetail,financialData"},
        )

    # -- Search ----------------------------------------------------------------

    def search(self, query: str, quotes_count: int = 10) -> list[dict]:
        """Search for tickers and companies.

        Args:
            query:        Search string.
            quotes_count: Max number of results.

        Returns:
            List of matching quote dicts.
        """
        data = self._get(
            "/v1/finance/search",
            params={"q": query, "quotesCount": quotes_count},
        )
        return data.get("quotes", [])

    # -- Trending & Movers -----------------------------------------------------

    def get_trending(self, region: str = "US", count: int = 20) -> list[dict]:
        """Get trending tickers.

        Args:
            region: Market region (e.g. "US", "GB").
            count:  Number of results.

        Returns:
            List of trending ticker dicts.
        """
        data = self._get(
            "/v1/finance/trending/US",
            params={"region": region, "count": count},
        )
        results = data.get("finance", {}).get("result", [])
        return results[0].get("quotes", []) if results else []

    def get_movers(
        self, category: str = "gainers", count: int = 25
    ) -> list[dict]:
        """Get market movers.

        Args:
            category: "gainers", "losers", or "actives".
            count:    Number of results.

        Returns:
            List of mover dicts.
        """
        data = self._get(
            f"/v1/finance/screener/predefined/saved",
            params={"scrIds": f"day_{category}", "count": count},
        )
        result = data.get("finance", {}).get("result", [])
        return result[0].get("quotes", []) if result else []

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
