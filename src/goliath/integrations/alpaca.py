"""
Alpaca Integration — stock and crypto trading, market data, and account management via the Alpaca API.

SETUP INSTRUCTIONS
==================

1. Sign up at https://alpaca.markets/ (paper or live trading).

2. Go to the dashboard and navigate to API Keys
   (https://app.alpaca.markets/paper/dashboard/overview for paper trading).

3. Click "Generate New Keys" and copy both the API Key ID and Secret Key.

4. Add to your .env:
     ALPACA_API_KEY=your-api-key-id
     ALPACA_API_SECRET=your-secret-key

5. For paper trading (default):
     ALPACA_PAPER=true

   For live trading:
     ALPACA_PAPER=false

IMPORTANT NOTES
===============
- API docs: https://docs.alpaca.markets/
- Paper trading base: https://paper-api.alpaca.markets
- Live trading base: https://api.alpaca.markets
- Market data base: https://data.alpaca.markets
- Rate limits: 200 requests/minute per API key.
- Authentication: APCA-API-KEY-ID and APCA-API-SECRET-KEY headers.
- Paper trading uses real market data with fake money.

Usage:
    from goliath.integrations.alpaca import AlpacaClient

    alp = AlpacaClient()

    # Get account info
    account = alp.get_account()

    # List positions
    positions = alp.list_positions()

    # Get a specific position
    pos = alp.get_position("AAPL")

    # Place a market order
    order = alp.place_order(
        symbol="AAPL",
        qty=10,
        side="buy",
        order_type="market",
        time_in_force="day",
    )

    # Place a limit order
    order = alp.place_order(
        symbol="MSFT",
        qty=5,
        side="buy",
        order_type="limit",
        time_in_force="gtc",
        limit_price=400.00,
    )

    # List open orders
    orders = alp.list_orders(status="open")

    # Cancel an order
    alp.cancel_order("order-id")

    # Cancel all orders
    alp.cancel_all_orders()

    # List assets
    assets = alp.list_assets(status="active", asset_class="us_equity")

    # Get asset details
    asset = alp.get_asset("AAPL")

    # Get bars (historical data)
    bars = alp.get_bars("AAPL", timeframe="1Day", start="2025-01-01", end="2025-01-31")

    # Get latest quote
    quote = alp.get_latest_quote("AAPL")

    # Get latest trade
    trade = alp.get_latest_trade("AAPL")

    # Get portfolio history
    history = alp.get_portfolio_history(period="1M", timeframe="1D")

    # List watchlists
    watchlists = alp.list_watchlists()
"""

import requests

from goliath import config

_PAPER_BASE = "https://paper-api.alpaca.markets"
_LIVE_BASE = "https://api.alpaca.markets"
_DATA_BASE = "https://data.alpaca.markets"


class AlpacaClient:
    """Alpaca REST API client for trading, positions, and market data."""

    def __init__(self):
        if not config.ALPACA_API_KEY or not config.ALPACA_API_SECRET:
            raise RuntimeError(
                "ALPACA_API_KEY and ALPACA_API_SECRET must both be set. "
                "Add them to .env or export as environment variables. "
                "See integrations/alpaca.py for setup instructions."
            )

        is_paper = (
            getattr(config, "ALPACA_PAPER", "true") or "true"
        ).lower() in ("true", "1", "yes")
        self.base_url = _PAPER_BASE if is_paper else _LIVE_BASE

        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": config.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET,
            "Content-Type": "application/json",
        })

    # -- Account ---------------------------------------------------------------

    def get_account(self) -> dict:
        """Get account information (buying power, equity, etc.).

        Returns:
            Account dict.
        """
        return self._get("/v2/account")

    def get_portfolio_history(
        self,
        period: str = "1M",
        timeframe: str = "1D",
        extended_hours: bool = False,
    ) -> dict:
        """Get portfolio value history.

        Args:
            period:         Time period ("1D","1W","1M","3M","1A","all").
            timeframe:      Bar size ("1Min","5Min","15Min","1H","1D").
            extended_hours: Include extended hours data.

        Returns:
            Portfolio history dict with timestamps and equity arrays.
        """
        return self._get(
            "/v2/account/portfolio/history",
            params={
                "period": period,
                "timeframe": timeframe,
                "extended_hours": str(extended_hours).lower(),
            },
        )

    # -- Orders ----------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        qty: float | None = None,
        notional: float | None = None,
        side: str = "buy",
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: float | None = None,
        stop_price: float | None = None,
        **kwargs,
    ) -> dict:
        """Place an order.

        Args:
            symbol:        Ticker symbol.
            qty:           Number of shares (use qty or notional, not both).
            notional:      Dollar amount (fractional shares).
            side:          "buy" or "sell".
            order_type:    "market", "limit", "stop", "stop_limit", "trailing_stop".
            time_in_force: "day", "gtc", "opg", "cls", "ioc", "fok".
            limit_price:   Limit price (for limit/stop_limit orders).
            stop_price:    Stop price (for stop/stop_limit orders).
            kwargs:        Additional fields (trail_percent, trail_price, etc.).

        Returns:
            Created order dict.
        """
        payload: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
            **kwargs,
        }
        if qty is not None:
            payload["qty"] = str(qty)
        if notional is not None:
            payload["notional"] = str(notional)
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)

        return self._post("/v2/orders", json=payload)

    def list_orders(
        self,
        status: str = "open",
        limit: int = 50,
        direction: str = "desc",
    ) -> list[dict]:
        """List orders.

        Args:
            status:    "open", "closed", or "all".
            limit:     Max results (max 500).
            direction: "asc" or "desc".

        Returns:
            List of order dicts.
        """
        return self._get(
            "/v2/orders",
            params={"status": status, "limit": limit, "direction": direction},
        )

    def get_order(self, order_id: str) -> dict:
        """Get order details.

        Args:
            order_id: Order UUID.

        Returns:
            Order dict.
        """
        return self._get(f"/v2/orders/{order_id}")

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an order.

        Args:
            order_id: Order UUID.

        Returns:
            Cancellation result.
        """
        resp = self.session.delete(f"{self.base_url}/v2/orders/{order_id}")
        resp.raise_for_status()
        return {"status": "cancelled"}

    def cancel_all_orders(self) -> list[dict]:
        """Cancel all open orders.

        Returns:
            List of cancellation results.
        """
        resp = self.session.delete(f"{self.base_url}/v2/orders")
        resp.raise_for_status()
        return resp.json() if resp.content else []

    # -- Positions -------------------------------------------------------------

    def list_positions(self) -> list[dict]:
        """List all open positions.

        Returns:
            List of position dicts.
        """
        return self._get("/v2/positions")

    def get_position(self, symbol: str) -> dict:
        """Get position for a specific symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            Position dict.
        """
        return self._get(f"/v2/positions/{symbol}")

    def close_position(self, symbol: str, qty: float | None = None) -> dict:
        """Close a position (sell all or partial).

        Args:
            symbol: Ticker symbol.
            qty:    Number of shares to sell (omit for all).

        Returns:
            Close order dict.
        """
        params: dict = {}
        if qty is not None:
            params["qty"] = str(qty)
        resp = self.session.delete(
            f"{self.base_url}/v2/positions/{symbol}", params=params
        )
        resp.raise_for_status()
        return resp.json()

    def close_all_positions(self) -> list[dict]:
        """Close all positions.

        Returns:
            List of close order results.
        """
        resp = self.session.delete(f"{self.base_url}/v2/positions")
        resp.raise_for_status()
        return resp.json() if resp.content else []

    # -- Assets ----------------------------------------------------------------

    def list_assets(
        self,
        status: str = "active",
        asset_class: str | None = None,
    ) -> list[dict]:
        """List assets.

        Args:
            status:      "active" or "inactive".
            asset_class: "us_equity" or "crypto".

        Returns:
            List of asset dicts.
        """
        params: dict = {"status": status}
        if asset_class:
            params["asset_class"] = asset_class
        return self._get("/v2/assets", params=params)

    def get_asset(self, symbol: str) -> dict:
        """Get asset details.

        Args:
            symbol: Ticker symbol or asset ID.

        Returns:
            Asset dict.
        """
        return self._get(f"/v2/assets/{symbol}")

    # -- Market Data -----------------------------------------------------------

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
        feed: str = "iex",
    ) -> dict:
        """Get historical bars (OHLCV).

        Args:
            symbol:    Ticker symbol.
            timeframe: Bar size ("1Min","5Min","15Min","30Min","1Hour","1Day","1Week","1Month").
            start:     Start date (RFC3339 or YYYY-MM-DD).
            end:       End date.
            limit:     Max bars (max 10000).
            feed:      Data feed ("iex", "sip").

        Returns:
            Dict with "bars" list.
        """
        params: dict = {
            "timeframe": timeframe,
            "limit": limit,
            "feed": feed,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return self._data_get(f"/v2/stocks/{symbol}/bars", params=params)

    def get_latest_quote(self, symbol: str, feed: str = "iex") -> dict:
        """Get latest quote (NBBO).

        Args:
            symbol: Ticker symbol.
            feed:   Data feed ("iex", "sip").

        Returns:
            Quote dict.
        """
        data = self._data_get(
            f"/v2/stocks/{symbol}/quotes/latest", params={"feed": feed}
        )
        return data.get("quote", data)

    def get_latest_trade(self, symbol: str, feed: str = "iex") -> dict:
        """Get latest trade.

        Args:
            symbol: Ticker symbol.
            feed:   Data feed.

        Returns:
            Trade dict.
        """
        data = self._data_get(
            f"/v2/stocks/{symbol}/trades/latest", params={"feed": feed}
        )
        return data.get("trade", data)

    def get_snapshot(self, symbol: str, feed: str = "iex") -> dict:
        """Get snapshot (latest trade, quote, minute bar, daily bar, prev daily bar).

        Args:
            symbol: Ticker symbol.
            feed:   Data feed.

        Returns:
            Snapshot dict.
        """
        return self._data_get(
            f"/v2/stocks/{symbol}/snapshot", params={"feed": feed}
        )

    # -- Watchlists ------------------------------------------------------------

    def list_watchlists(self) -> list[dict]:
        """List watchlists.

        Returns:
            List of watchlist dicts.
        """
        return self._get("/v2/watchlists")

    def create_watchlist(self, name: str, symbols: list[str] | None = None) -> dict:
        """Create a watchlist.

        Args:
            name:    Watchlist name.
            symbols: Initial ticker symbols.

        Returns:
            Created watchlist dict.
        """
        payload: dict = {"name": name}
        if symbols:
            payload["symbols"] = symbols
        return self._post("/v2/watchlists", json=payload)

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _data_get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_DATA_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
