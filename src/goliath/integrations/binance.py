"""
Binance Integration — market data, account info, and trading via the Binance API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.binance.com/ and create an account.

2. Go to API Management (https://www.binance.com/en/my/settings/api-management).

3. Create a new API key and copy the API Key and Secret Key.

4. Add to your .env:
     BINANCE_API_KEY=your_api_key_here
     BINANCE_API_SECRET=your_secret_key_here

IMPORTANT NOTES
===============
- API docs: https://binance-docs.github.io/apidocs/spot/en/
- Public endpoints (market data) do NOT require authentication.
- Authenticated endpoints (account, trading) require HMAC-SHA256 signed requests.
- Rate limits: 1200 requests/minute for order endpoints, 6000/minute for others.
- For US users, use Binance.US (api.binance.us) — set BINANCE_BASE_URL in .env.
- This client covers public market data; for signed endpoints, the secret key is required.

Usage:
    from goliath.integrations.binance import BinanceClient

    b = BinanceClient()

    # Get current price
    price = b.get_price("BTCUSDT")

    # Get all prices
    prices = b.get_all_prices()

    # Get order book
    book = b.get_order_book("ETHUSDT", limit=10)

    # Get recent trades
    trades = b.get_recent_trades("BTCUSDT", limit=20)

    # Get candlestick / kline data
    candles = b.get_klines("BTCUSDT", interval="1h", limit=24)

    # Get 24h ticker stats
    stats = b.get_24h_stats("BTCUSDT")

    # Get exchange info
    info = b.get_exchange_info()

    # Get account info (requires API key + secret)
    account = b.get_account()
"""

import hashlib
import hmac
import time

import requests

from goliath import config

_DEFAULT_BASE = "https://api.binance.com"


class BinanceClient:
    """Binance API client for market data, account info, and trading."""

    def __init__(self):
        self.api_key = config.BINANCE_API_KEY or ""
        self.api_secret = config.BINANCE_API_SECRET or ""
        self.base_url = getattr(config, "BINANCE_BASE_URL", "") or _DEFAULT_BASE

        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # -- Market Data (Public) ----------------------------------------------

    def get_price(self, symbol: str) -> dict:
        """Get current price for a symbol.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT", "ETHBTC").

        Returns:
            Dict with "symbol" and "price".
        """
        return self._get("/api/v3/ticker/price", params={"symbol": symbol})

    def get_all_prices(self) -> list[dict]:
        """Get current prices for all symbols.

        Returns:
            List of dicts with "symbol" and "price".
        """
        return self._get("/api/v3/ticker/price")

    def get_order_book(self, symbol: str, limit: int = 100) -> dict:
        """Get order book (bids and asks).

        Args:
            symbol: Trading pair.
            limit:  Depth (5, 10, 20, 50, 100, 500, 1000, 5000).

        Returns:
            Dict with "bids" and "asks" lists.
        """
        return self._get(
            "/api/v3/depth",
            params={"symbol": symbol, "limit": limit},
        )

    def get_recent_trades(self, symbol: str, limit: int = 500) -> list[dict]:
        """Get recent trades.

        Args:
            symbol: Trading pair.
            limit:  Number of trades (max 1000).

        Returns:
            List of trade dicts.
        """
        return self._get(
            "/api/v3/trades",
            params={"symbol": symbol, "limit": limit},
        )

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[list]:
        """Get candlestick / kline data.

        Args:
            symbol:     Trading pair.
            interval:   Kline interval ("1m","3m","5m","15m","30m","1h","2h","4h",
                        "6h","8h","12h","1d","3d","1w","1M").
            limit:      Number of candles (max 1000).
            start_time: Start time in milliseconds.
            end_time:   End time in milliseconds.

        Returns:
            List of kline arrays [open_time, open, high, low, close, volume, ...].
        """
        params: dict = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return self._get("/api/v3/klines", params=params)

    def get_24h_stats(self, symbol: str | None = None) -> dict | list:
        """Get 24-hour rolling ticker statistics.

        Args:
            symbol: Trading pair. If None, returns stats for all symbols.

        Returns:
            Stats dict (single symbol) or list of stats dicts (all symbols).
        """
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/api/v3/ticker/24hr", params=params)

    def get_exchange_info(self, symbol: str | None = None) -> dict:
        """Get exchange trading rules and symbol information.

        Args:
            symbol: Optional symbol to filter.

        Returns:
            Exchange info dict with "symbols" list.
        """
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/api/v3/exchangeInfo", params=params)

    def get_avg_price(self, symbol: str) -> dict:
        """Get current average price for a symbol.

        Args:
            symbol: Trading pair.

        Returns:
            Dict with "mins" (interval) and "price".
        """
        return self._get("/api/v3/avgPrice", params={"symbol": symbol})

    # -- Account (Signed) --------------------------------------------------

    def get_account(self) -> dict:
        """Get account information (requires API key and secret).

        Returns:
            Account dict with balances, permissions, etc.
        """
        return self._signed_get("/api/v3/account")

    def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Get open orders (requires API key and secret).

        Args:
            symbol: Optional trading pair filter.

        Returns:
            List of open order dicts.
        """
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_get("/api/v3/openOrders", extra_params=params)

    def get_trade_history(self, symbol: str, limit: int = 500) -> list[dict]:
        """Get account trade history (requires API key and secret).

        Args:
            symbol: Trading pair.
            limit:  Number of trades (max 1000).

        Returns:
            List of trade dicts.
        """
        return self._signed_get(
            "/api/v3/myTrades",
            extra_params={"symbol": symbol, "limit": limit},
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _signed_get(self, path: str, extra_params: dict | None = None) -> dict | list:
        """Make a signed GET request (HMAC-SHA256)."""
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "BINANCE_API_KEY and BINANCE_API_SECRET are required for "
                "authenticated endpoints. See integrations/binance.py for setup."
            )

        params = extra_params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000

        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode(), query_string.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = signature

        resp = self.session.get(f"{self.base_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json()
