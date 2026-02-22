"""
Kraken Integration — market data, account balances, and trading via the Kraken REST API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.kraken.com/ and create an account.

2. Navigate to Settings > API (https://www.kraken.com/u/security/api).

3. Click "Generate New Key" and select the permissions you need.

4. Copy the API Key and Private Key and add to your .env:
     KRAKEN_API_KEY=your-api-key
     KRAKEN_API_SECRET=your-private-key-base64

IMPORTANT NOTES
===============
- API docs: https://docs.kraken.com/rest/
- Public endpoints require no authentication.
- Private endpoints use a nonce + HMAC-SHA512 signature scheme.
- Rate limits: ~15 calls per decay period (varies by endpoint tier).
- Base URL: https://api.kraken.com

Usage:
    from goliath.integrations.kraken import KrakenClient

    kr = KrakenClient()

    # Get ticker info
    ticker = kr.get_ticker("XBTUSD")

    # Get order book
    book = kr.get_order_book("XBTUSD", count=10)

    # Get OHLC data
    ohlc = kr.get_ohlc("XBTUSD", interval=60)

    # Get recent trades
    trades = kr.get_recent_trades("XBTUSD")

    # Get tradable asset pairs
    pairs = kr.get_asset_pairs()

    # Get asset info
    assets = kr.get_assets()

    # Get server time
    server_time = kr.get_server_time()

    # Get account balance (requires auth)
    balance = kr.get_balance()

    # Get trade balance (requires auth)
    trade_balance = kr.get_trade_balance()

    # Get open orders (requires auth)
    orders = kr.get_open_orders()
"""

import base64
import hashlib
import hmac
import time
import urllib.parse

import requests

from goliath import config

_API_BASE = "https://api.kraken.com"


class KrakenClient:
    """Kraken REST API client for market data and trading."""

    def __init__(self):
        self.api_key = getattr(config, "KRAKEN_API_KEY", "") or ""
        self.api_secret = getattr(config, "KRAKEN_API_SECRET", "") or ""

        self.session = requests.Session()

    # -- Public Market Data ----------------------------------------------------

    def get_server_time(self) -> dict:
        """Get server time.

        Returns:
            Dict with "unixtime" and "rfc1123".
        """
        return self._public_get("/0/public/Time")

    def get_assets(self, assets: str | None = None) -> dict:
        """Get asset information.

        Args:
            assets: Comma-separated asset names (e.g. "XBT,ETH"). None for all.

        Returns:
            Dict of asset info keyed by asset name.
        """
        params: dict = {}
        if assets:
            params["asset"] = assets
        return self._public_get("/0/public/Assets", params=params)

    def get_asset_pairs(self, pair: str | None = None) -> dict:
        """Get tradable asset pairs.

        Args:
            pair: Comma-separated pair names (e.g. "XBTUSD,ETHUSD"). None for all.

        Returns:
            Dict of pair info keyed by pair name.
        """
        params: dict = {}
        if pair:
            params["pair"] = pair
        return self._public_get("/0/public/AssetPairs", params=params)

    def get_ticker(self, pair: str) -> dict:
        """Get ticker information.

        Args:
            pair: Asset pair (e.g. "XBTUSD", "ETHUSD").

        Returns:
            Dict of ticker data keyed by pair name.
        """
        return self._public_get("/0/public/Ticker", params={"pair": pair})

    def get_ohlc(
        self,
        pair: str,
        interval: int = 1,
        since: int | None = None,
    ) -> dict:
        """Get OHLC (candlestick) data.

        Args:
            pair:     Asset pair.
            interval: Time frame in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600).
            since:    Return data since this UNIX timestamp.

        Returns:
            Dict with pair data and "last" timestamp.
        """
        params: dict = {"pair": pair, "interval": interval}
        if since:
            params["since"] = since
        return self._public_get("/0/public/OHLC", params=params)

    def get_order_book(self, pair: str, count: int = 100) -> dict:
        """Get order book.

        Args:
            pair:  Asset pair.
            count: Max depth (max 500).

        Returns:
            Dict with "asks" and "bids".
        """
        return self._public_get(
            "/0/public/Depth", params={"pair": pair, "count": count}
        )

    def get_recent_trades(self, pair: str, since: int | None = None) -> dict:
        """Get recent trades.

        Args:
            pair:  Asset pair.
            since: Return trades since this trade ID.

        Returns:
            Dict with trade data and "last" ID.
        """
        params: dict = {"pair": pair}
        if since:
            params["since"] = since
        return self._public_get("/0/public/Trades", params=params)

    def get_recent_spreads(self, pair: str, since: int | None = None) -> dict:
        """Get recent spread data.

        Args:
            pair:  Asset pair.
            since: Return spreads since this UNIX timestamp.

        Returns:
            Dict with spread data.
        """
        params: dict = {"pair": pair}
        if since:
            params["since"] = since
        return self._public_get("/0/public/Spread", params=params)

    # -- Private (Authenticated) -----------------------------------------------

    def get_balance(self) -> dict:
        """Get account balance (requires auth).

        Returns:
            Dict of asset balances.
        """
        return self._private_post("/0/private/Balance")

    def get_trade_balance(self, asset: str = "ZUSD") -> dict:
        """Get trade balance summary (requires auth).

        Args:
            asset: Base asset for calculations (default "ZUSD").

        Returns:
            Dict with equity, free margin, trade balance, etc.
        """
        return self._private_post("/0/private/TradeBalance", data={"asset": asset})

    def get_open_orders(self) -> dict:
        """Get open orders (requires auth).

        Returns:
            Dict with "open" orders mapping.
        """
        return self._private_post("/0/private/OpenOrders")

    def get_closed_orders(self) -> dict:
        """Get closed orders (requires auth).

        Returns:
            Dict with "closed" orders mapping.
        """
        return self._private_post("/0/private/ClosedOrders")

    def get_trades_history(self) -> dict:
        """Get trade history (requires auth).

        Returns:
            Dict with "trades" mapping and "count".
        """
        return self._private_post("/0/private/TradesHistory")

    # -- internal helpers ------------------------------------------------------

    def _public_get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        if body.get("error"):
            raise RuntimeError(f"Kraken API error: {body['error']}")
        return body.get("result", body)

    def _private_post(self, path: str, data: dict | None = None) -> dict:
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "KRAKEN_API_KEY and KRAKEN_API_SECRET are required for "
                "private endpoints. See integrations/kraken.py for setup."
            )

        data = data or {}
        data["nonce"] = str(int(time.time() * 1000))

        post_data = urllib.parse.urlencode(data)
        encoded = (data["nonce"] + post_data).encode()
        message = path.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(
            base64.b64decode(self.api_secret), message, hashlib.sha512
        )

        headers = {
            "API-Key": self.api_key,
            "API-Sign": base64.b64encode(signature.digest()).decode(),
        }
        resp = self.session.post(
            f"{_API_BASE}{path}", data=data, headers=headers
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("error"):
            raise RuntimeError(f"Kraken API error: {body['error']}")
        return body.get("result", body)
