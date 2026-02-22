"""
Robinhood Integration — stock quotes, positions, watchlists, and account data via the Robinhood API.

SETUP INSTRUCTIONS
==================

1. You need a Robinhood account at https://robinhood.com/.

2. Robinhood does not offer a public API. This integration uses the
   unofficial internal API endpoints. You must authenticate with your
   Robinhood credentials or supply an access token.

3. Add to your .env:
     ROBINHOOD_ACCESS_TOKEN=your-bearer-token

   To obtain a token, log in via the OAuth endpoint (see below) or
   extract it from an authenticated browser/app session.

4. Alternatively, supply username/password + MFA for automatic login:
     ROBINHOOD_USERNAME=your-email@example.com
     ROBINHOOD_PASSWORD=your-password
     ROBINHOOD_MFA_CODE=123456

   (MFA code is a one-time TOTP — you may need to re-generate each session.)

IMPORTANT NOTES
===============
- Robinhood has NO official public API. These endpoints are reverse-engineered.
- Endpoints may break without notice.
- Base URL: https://api.robinhood.com
- Rate limits: undocumented, be conservative.
- For production use, consider official broker APIs (Alpaca, Interactive Brokers).
- Authentication: Bearer token in Authorization header.

Usage:
    from goliath.integrations.robinhood import RobinhoodClient

    rh = RobinhoodClient()

    # Get account info
    account = rh.get_account()

    # Get portfolio
    portfolio = rh.get_portfolio()

    # List positions
    positions = rh.list_positions()

    # Get a stock quote
    quote = rh.get_quote("AAPL")

    # Get multiple quotes
    quotes = rh.get_quotes(["AAPL", "MSFT", "GOOG"])

    # Get fundamentals
    fundamentals = rh.get_fundamentals("AAPL")

    # Search instruments
    results = rh.search_instruments("Tesla")

    # Get instrument by symbol
    instrument = rh.get_instrument_by_symbol("AAPL")

    # Get watchlist
    watchlist = rh.get_watchlist()

    # Get historical data
    history = rh.get_historicals("AAPL", interval="day", span="month")

    # Get movers
    movers = rh.get_movers(direction="up")

    # Get earnings for a symbol
    earnings = rh.get_earnings("AAPL")

    # Get news for a symbol
    news = rh.get_news("AAPL")

    # Get popularity (number of holders on Robinhood)
    popularity = rh.get_popularity("AAPL")
"""

import requests

from goliath import config

_API_BASE = "https://api.robinhood.com"


class RobinhoodClient:
    """Robinhood API client for quotes, positions, and account data."""

    def __init__(self):
        token = getattr(config, "ROBINHOOD_ACCESS_TOKEN", "") or ""

        if not token:
            # Attempt login with username/password
            username = getattr(config, "ROBINHOOD_USERNAME", "") or ""
            password = getattr(config, "ROBINHOOD_PASSWORD", "") or ""
            if username and password:
                token = self._login(username, password)
            else:
                raise RuntimeError(
                    "ROBINHOOD_ACCESS_TOKEN is not set and no username/password "
                    "provided. Add ROBINHOOD_ACCESS_TOKEN to .env, or set both "
                    "ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD. "
                    "See integrations/robinhood.py for setup instructions."
                )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "GOLIATH/1.0",
        })

    # -- Account & Portfolio ---------------------------------------------------

    def get_account(self) -> dict:
        """Get primary account info.

        Returns:
            Account dict with buying power, cash, etc.
        """
        data = self._get("/accounts/")
        results = data.get("results", [])
        return results[0] if results else data

    def get_portfolio(self) -> dict:
        """Get portfolio summary (equity, returns, etc.).

        Returns:
            Portfolio dict.
        """
        account = self.get_account()
        account_number = account.get("account_number", "")
        if not account_number:
            raise RuntimeError("Could not determine account number.")
        return self._get(f"/portfolios/{account_number}/")

    # -- Positions -------------------------------------------------------------

    def list_positions(self, nonzero: bool = True) -> list[dict]:
        """List stock positions.

        Args:
            nonzero: Only return positions with shares > 0.

        Returns:
            List of position dicts.
        """
        params: dict = {}
        if nonzero:
            params["nonzero"] = "true"
        data = self._get("/positions/", params=params)
        return data.get("results", [])

    # -- Quotes & Market Data --------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """Get a stock quote.

        Args:
            symbol: Ticker symbol.

        Returns:
            Quote dict with price, bid, ask, volume, etc.
        """
        return self._get(f"/quotes/{symbol.upper()}/")

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Get quotes for multiple symbols.

        Args:
            symbols: List of ticker symbols.

        Returns:
            List of quote dicts.
        """
        data = self._get(
            "/quotes/",
            params={"symbols": ",".join(s.upper() for s in symbols)},
        )
        return data.get("results", [])

    def get_fundamentals(self, symbol: str) -> dict:
        """Get fundamental data for a symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            Fundamentals dict (PE ratio, market cap, dividend yield, etc.).
        """
        return self._get(f"/fundamentals/{symbol.upper()}/")

    def get_historicals(
        self,
        symbol: str,
        interval: str = "day",
        span: str = "month",
        bounds: str = "regular",
    ) -> dict:
        """Get historical price data.

        Args:
            symbol:   Ticker symbol.
            interval: "5minute", "10minute", "hour", "day", "week".
            span:     "day", "week", "month", "3month", "year", "5year", "all".
            bounds:   "regular", "extended", "trading".

        Returns:
            Dict with "historicals" list of OHLCV data points.
        """
        return self._get(
            f"/quotes/historicals/{symbol.upper()}/",
            params={"interval": interval, "span": span, "bounds": bounds},
        )

    # -- Instruments -----------------------------------------------------------

    def search_instruments(self, query: str) -> list[dict]:
        """Search for instruments by name or symbol.

        Args:
            query: Search query.

        Returns:
            List of instrument dicts.
        """
        data = self._get("/instruments/", params={"query": query})
        return data.get("results", [])

    def get_instrument_by_symbol(self, symbol: str) -> dict:
        """Get instrument details by ticker symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            Instrument dict.
        """
        data = self._get(
            "/instruments/", params={"symbol": symbol.upper()}
        )
        results = data.get("results", [])
        return results[0] if results else {}

    # -- Watchlist -------------------------------------------------------------

    def get_watchlist(self, name: str = "Default") -> list[dict]:
        """Get watchlist instruments.

        Args:
            name: Watchlist name (default "Default").

        Returns:
            List of watchlist item dicts.
        """
        data = self._get(f"/watchlists/{name}/")
        return data.get("results", [])

    # -- Movers ----------------------------------------------------------------

    def get_movers(self, direction: str = "up") -> list[dict]:
        """Get top movers.

        Args:
            direction: "up" or "down".

        Returns:
            List of mover dicts.
        """
        data = self._get(
            "/midlands/movers/sp500/",
            params={"direction": direction},
        )
        return data.get("results", [])

    # -- Earnings --------------------------------------------------------------

    def get_earnings(self, symbol: str) -> list[dict]:
        """Get earnings data for a symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            List of earnings dicts.
        """
        data = self._get(
            "/marketdata/earnings/",
            params={"symbol": symbol.upper()},
        )
        return data.get("results", [])

    # -- News ------------------------------------------------------------------

    def get_news(self, symbol: str, limit: int = 10) -> list[dict]:
        """Get news articles for a symbol.

        Args:
            symbol: Ticker symbol.
            limit:  Number of articles.

        Returns:
            List of news article dicts.
        """
        data = self._get(
            "/midlands/news/{symbol.upper()}/",
            params={"symbol": symbol.upper()},
        )
        return data.get("results", data) if isinstance(data, dict) else data

    # -- Popularity ------------------------------------------------------------

    def get_popularity(self, symbol: str) -> dict:
        """Get popularity data (number of Robinhood holders).

        Args:
            symbol: Ticker symbol.

        Returns:
            Dict with "num_open_positions".
        """
        instrument = self.get_instrument_by_symbol(symbol)
        instrument_id = instrument.get("id", "")
        if not instrument_id:
            raise ValueError(f"Instrument not found for {symbol}")
        return self._get(f"/instruments/{instrument_id}/popularity/")

    # -- Tags ------------------------------------------------------------------

    def get_tags(self, symbol: str) -> list[dict]:
        """Get tags/collections a symbol belongs to.

        Args:
            symbol: Ticker symbol.

        Returns:
            List of tag dicts.
        """
        instrument = self.get_instrument_by_symbol(symbol)
        instrument_id = instrument.get("id", "")
        if not instrument_id:
            return []
        data = self._get(f"/midlands/tags/instrument/{instrument_id}/")
        return data.get("tags", [])

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _login(username: str, password: str) -> str:
        """Authenticate with Robinhood and return an access token."""
        mfa_code = getattr(config, "ROBINHOOD_MFA_CODE", "") or ""

        payload: dict = {
            "grant_type": "password",
            "scope": "internal",
            "client_id": "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
            "username": username,
            "password": password,
            "device_token": "GOLIATH-device",
        }
        if mfa_code:
            payload["mfa_code"] = mfa_code

        resp = requests.post(
            f"{_API_BASE}/oauth2/token/",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

        token = data.get("access_token", "")
        if not token:
            if data.get("mfa_required"):
                raise RuntimeError(
                    "Robinhood MFA required. Set ROBINHOOD_MFA_CODE in .env "
                    "with your current TOTP code."
                )
            raise RuntimeError(f"Robinhood login failed: {data}")
        return token
