"""
TradingView Integration — technical analysis, screeners, and market data via TradingView APIs.

SETUP INSTRUCTIONS
==================

1. TradingView does not offer an official public REST API for individual use.
   This integration uses the TradingView unofficial data endpoints for
   symbol search, technical analysis, and screeners.

2. For authenticated features (alerts, saved charts), you can optionally set:
     TRADINGVIEW_SESSION_ID=your-session-id-cookie
     TRADINGVIEW_SESSION_SIGN=your-session-sign-cookie

   To get these, log in to tradingview.com and copy the "sessionid" and
   "sessionid_sign" cookies from your browser.

3. No API key is required for public data (search, screeners).

IMPORTANT NOTES
===============
- No official API — endpoints may change.
- Scanner: https://scanner.tradingview.com/
- Symbol search: https://symbol-search.tradingview.com/
- Rate limits are unofficial; be conservative.
- Technical analysis data comes from the screener API.
- For production use, consider TradingView's official data partners.

Usage:
    from goliath.integrations.tradingview import TradingViewClient

    tv = TradingViewClient()

    # Search for a symbol
    results = tv.search_symbol("AAPL")

    # Get technical analysis summary for a stock
    analysis = tv.get_analysis("AAPL", exchange="NASDAQ")

    # Screen stocks (custom filters)
    stocks = tv.screen_stocks(
        market="america",
        filters=[{"left": "close", "operation": "greater", "right": 100}],
        columns=["name", "close", "change", "volume"],
    )

    # Get forex analysis
    fx = tv.get_analysis("EURUSD", exchange="FX", screener="forex")

    # Get crypto analysis
    crypto = tv.get_analysis("BTCUSD", exchange="BITSTAMP", screener="crypto")

    # Screen crypto
    coins = tv.screen_crypto(
        columns=["name", "close", "change", "market_cap_calc"],
        sort_by="market_cap_calc",
    )
"""

import requests

from goliath import config

_SEARCH_URL = "https://symbol-search.tradingview.com/symbol_search/v3/"
_SCANNER_BASE = "https://scanner.tradingview.com"


class TradingViewClient:
    """TradingView client for symbol search, technical analysis, and screeners."""

    def __init__(self):
        session_id = getattr(config, "TRADINGVIEW_SESSION_ID", "") or ""
        session_sign = getattr(config, "TRADINGVIEW_SESSION_SIGN", "") or ""

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GOLIATH/1.0",
            "Content-Type": "application/json",
        })

        if session_id:
            self.session.cookies.set("sessionid", session_id)
        if session_sign:
            self.session.cookies.set("sessionid_sign", session_sign)

    # -- Symbol Search ---------------------------------------------------------

    def search_symbol(
        self,
        query: str,
        symbol_type: str | None = None,
        exchange: str | None = None,
        limit: int = 30,
    ) -> list[dict]:
        """Search for a symbol.

        Args:
            query:       Search query (e.g. "AAPL", "Tesla").
            symbol_type: Filter by type ("stock", "crypto", "forex", "index", "fund").
            exchange:    Filter by exchange (e.g. "NASDAQ", "NYSE").
            limit:       Max results.

        Returns:
            List of symbol dicts.
        """
        params: dict = {"text": query, "hl": "true", "lang": "en", "search_type": "undefined"}
        if symbol_type:
            params["type"] = symbol_type
        if exchange:
            params["exchange"] = exchange
        resp = self.session.get(_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("symbols", data) if isinstance(data, dict) else data
        return results[:limit] if isinstance(results, list) else []

    # -- Technical Analysis (via Screener) -------------------------------------

    def get_analysis(
        self,
        symbol: str,
        exchange: str = "NASDAQ",
        screener: str = "america",
    ) -> dict:
        """Get technical analysis data for a symbol.

        Args:
            symbol:   Symbol name (e.g. "AAPL", "EURUSD", "BTCUSD").
            exchange: Exchange name (e.g. "NASDAQ", "NYSE", "FX", "BITSTAMP").
            screener: Market screener ("america", "forex", "crypto", "cfd").

        Returns:
            Dict with technical analysis columns and values.
        """
        ticker = f"{exchange}:{symbol}"
        columns = [
            "Recommend.All", "Recommend.MA", "Recommend.Other",
            "RSI", "RSI[1]", "Stoch.K", "Stoch.D", "Stoch.K[1]", "Stoch.D[1]",
            "CCI20", "CCI20[1]", "ADX", "ADX+DI", "ADX-DI",
            "AO", "AO[1]", "Mom", "Mom[1]",
            "MACD.macd", "MACD.signal",
            "BB.lower", "BB.upper", "close",
            "EMA5", "EMA10", "EMA20", "EMA30", "EMA50", "EMA100", "EMA200",
            "SMA5", "SMA10", "SMA20", "SMA30", "SMA50", "SMA100", "SMA200",
            "open", "high", "low", "volume", "change", "change_abs",
        ]

        payload = {
            "symbols": {"tickers": [ticker], "query": {"types": []}},
            "columns": columns,
        }
        resp = self.session.post(
            f"{_SCANNER_BASE}/{screener}/scan", json=payload
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("data", [])
        if not results:
            return {}

        row = results[0]
        values = row.get("d", [])
        return dict(zip(columns, values))

    # -- Stock Screener --------------------------------------------------------

    def screen_stocks(
        self,
        market: str = "america",
        filters: list[dict] | None = None,
        columns: list[str] | None = None,
        sort_by: str = "volume",
        sort_order: str = "desc",
        limit: int = 50,
    ) -> list[dict]:
        """Screen stocks with custom filters.

        Args:
            market:     Market ("america", "uk", "india", "germany", etc.).
            filters:    List of filter dicts with "left", "operation", "right".
            columns:    Columns to return (e.g. ["name","close","change","volume"]).
            sort_by:    Column to sort by.
            sort_order: "asc" or "desc".
            limit:      Max results.

        Returns:
            List of stock dicts.
        """
        cols = columns or [
            "name", "description", "close", "change", "change_abs",
            "volume", "market_cap_basic",
        ]
        payload: dict = {
            "columns": cols,
            "sort": {"sortBy": sort_by, "sortOrder": sort_order},
            "range": [0, limit],
        }
        if filters:
            payload["filter"] = filters

        resp = self.session.post(
            f"{_SCANNER_BASE}/{market}/scan", json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"symbol": row.get("s", ""), **dict(zip(cols, row.get("d", [])))}
            for row in data.get("data", [])
        ]

    # -- Crypto Screener -------------------------------------------------------

    def screen_crypto(
        self,
        columns: list[str] | None = None,
        sort_by: str = "market_cap_calc",
        sort_order: str = "desc",
        limit: int = 50,
    ) -> list[dict]:
        """Screen cryptocurrencies.

        Args:
            columns:    Columns to return.
            sort_by:    Column to sort by.
            sort_order: "asc" or "desc".
            limit:      Max results.

        Returns:
            List of crypto dicts.
        """
        cols = columns or [
            "name", "description", "close", "change",
            "volume", "market_cap_calc",
        ]
        return self.screen_stocks(
            market="crypto",
            columns=cols,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )

    # -- Forex Screener --------------------------------------------------------

    def screen_forex(
        self,
        columns: list[str] | None = None,
        sort_by: str = "name",
        limit: int = 50,
    ) -> list[dict]:
        """Screen forex pairs.

        Args:
            columns: Columns to return.
            sort_by: Column to sort by.
            limit:   Max results.

        Returns:
            List of forex pair dicts.
        """
        cols = columns or [
            "name", "description", "close", "change", "change_abs",
            "bid", "ask", "high", "low",
        ]
        return self.screen_stocks(
            market="forex", columns=cols, sort_by=sort_by, limit=limit
        )
