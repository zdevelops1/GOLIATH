"""
Alpha Vantage Integration — stocks, forex, crypto, and economic indicators via the Alpha Vantage API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.alphavantage.co/ and click "Get your free API key".

2. Fill in the form and copy your API key.

3. Add to your .env:
     ALPHA_VANTAGE_API_KEY=your-api-key

IMPORTANT NOTES
===============
- API docs: https://www.alphavantage.co/documentation/
- Free tier: 25 requests/day, 5 requests/minute.
- Premium plans: https://www.alphavantage.co/premium/
- Base URL: https://www.alphavantage.co/query
- All endpoints use GET with query parameters.

Usage:
    from goliath.integrations.alpha_vantage import AlphaVantageClient

    av = AlphaVantageClient()

    # Get stock quote
    quote = av.get_quote("AAPL")

    # Search for symbols
    results = av.search_symbol("Tesla")

    # Get intraday time series
    data = av.get_intraday("AAPL", interval="5min")

    # Get daily time series
    daily = av.get_daily("MSFT")

    # Get weekly time series
    weekly = av.get_weekly("GOOG")

    # Get forex exchange rate
    fx = av.get_fx_rate("EUR", "USD")

    # Get crypto rating
    rating = av.get_crypto_rating("BTC")

    # Get digital currency daily
    crypto = av.get_crypto_daily("BTC", market="USD")

    # Get GDP data
    gdp = av.get_real_gdp()

    # Get inflation data
    inflation = av.get_inflation()
"""

import requests

from goliath import config

_API_BASE = "https://www.alphavantage.co/query"


class AlphaVantageClient:
    """Alpha Vantage API client for stocks, forex, crypto, and economic data."""

    def __init__(self):
        if not config.ALPHA_VANTAGE_API_KEY:
            raise RuntimeError(
                "ALPHA_VANTAGE_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/alpha_vantage.py for setup instructions."
            )

        self.api_key = config.ALPHA_VANTAGE_API_KEY
        self.session = requests.Session()

    # -- Stock Data ------------------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """Get real-time stock quote.

        Args:
            symbol: Stock ticker (e.g. "AAPL", "MSFT").

        Returns:
            Quote dict with price, volume, change, etc.
        """
        data = self._get(function="GLOBAL_QUOTE", symbol=symbol)
        return data.get("Global Quote", data)

    def search_symbol(self, keywords: str) -> list[dict]:
        """Search for stock symbols by name or keyword.

        Args:
            keywords: Search query (e.g. "Tesla", "Microsoft").

        Returns:
            List of matching symbol dicts.
        """
        data = self._get(function="SYMBOL_SEARCH", keywords=keywords)
        return data.get("bestMatches", [])

    def get_intraday(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: str = "compact",
    ) -> dict:
        """Get intraday time series.

        Args:
            symbol:     Stock ticker.
            interval:   Time interval ("1min","5min","15min","30min","60min").
            outputsize: "compact" (100 points) or "full".

        Returns:
            Time series dict.
        """
        return self._get(
            function="TIME_SERIES_INTRADAY",
            symbol=symbol, interval=interval, outputsize=outputsize,
        )

    def get_daily(self, symbol: str, outputsize: str = "compact") -> dict:
        """Get daily time series.

        Args:
            symbol:     Stock ticker.
            outputsize: "compact" (100 days) or "full" (20+ years).

        Returns:
            Time series dict.
        """
        return self._get(
            function="TIME_SERIES_DAILY",
            symbol=symbol, outputsize=outputsize,
        )

    def get_weekly(self, symbol: str) -> dict:
        """Get weekly time series.

        Args:
            symbol: Stock ticker.

        Returns:
            Time series dict.
        """
        return self._get(function="TIME_SERIES_WEEKLY", symbol=symbol)

    def get_monthly(self, symbol: str) -> dict:
        """Get monthly time series.

        Args:
            symbol: Stock ticker.

        Returns:
            Time series dict.
        """
        return self._get(function="TIME_SERIES_MONTHLY", symbol=symbol)

    # -- Forex -----------------------------------------------------------------

    def get_fx_rate(self, from_currency: str, to_currency: str) -> dict:
        """Get real-time forex exchange rate.

        Args:
            from_currency: Source currency code (e.g. "EUR").
            to_currency:   Target currency code (e.g. "USD").

        Returns:
            Exchange rate dict.
        """
        data = self._get(
            function="CURRENCY_EXCHANGE_RATE",
            from_currency=from_currency, to_currency=to_currency,
        )
        return data.get("Realtime Currency Exchange Rate", data)

    def get_fx_daily(
        self, from_symbol: str, to_symbol: str, outputsize: str = "compact"
    ) -> dict:
        """Get daily forex time series.

        Args:
            from_symbol: Source currency.
            to_symbol:   Target currency.
            outputsize:  "compact" or "full".

        Returns:
            Time series dict.
        """
        return self._get(
            function="FX_DAILY",
            from_symbol=from_symbol, to_symbol=to_symbol,
            outputsize=outputsize,
        )

    # -- Crypto ----------------------------------------------------------------

    def get_crypto_rating(self, symbol: str) -> dict:
        """Get crypto health rating (FCAS score).

        Args:
            symbol: Crypto symbol (e.g. "BTC", "ETH").

        Returns:
            Rating dict.
        """
        data = self._get(function="CRYPTO_RATING", symbol=symbol)
        return data.get("Crypto Rating (FCAS)", data)

    def get_crypto_daily(
        self, symbol: str, market: str = "USD"
    ) -> dict:
        """Get daily crypto prices.

        Args:
            symbol: Crypto symbol (e.g. "BTC").
            market: Market currency (e.g. "USD", "EUR").

        Returns:
            Time series dict.
        """
        return self._get(
            function="DIGITAL_CURRENCY_DAILY",
            symbol=symbol, market=market,
        )

    # -- Economic Indicators ---------------------------------------------------

    def get_real_gdp(self, interval: str = "annual") -> dict:
        """Get US real GDP data.

        Args:
            interval: "annual" or "quarterly".

        Returns:
            GDP data dict with "data" list.
        """
        return self._get(function="REAL_GDP", interval=interval)

    def get_inflation(self) -> dict:
        """Get US inflation (CPI) data.

        Returns:
            Inflation data dict with "data" list.
        """
        return self._get(function="INFLATION")

    def get_federal_funds_rate(self, interval: str = "monthly") -> dict:
        """Get federal funds interest rate.

        Args:
            interval: "daily", "weekly", or "monthly".

        Returns:
            Interest rate data dict.
        """
        return self._get(function="FEDERAL_FUNDS_RATE", interval=interval)

    def get_unemployment(self) -> dict:
        """Get US unemployment rate.

        Returns:
            Unemployment data dict with "data" list.
        """
        return self._get(function="UNEMPLOYMENT")

    # -- Technical Indicators --------------------------------------------------

    def get_sma(
        self, symbol: str, interval: str = "daily",
        time_period: int = 20, series_type: str = "close",
    ) -> dict:
        """Get Simple Moving Average (SMA).

        Args:
            symbol:      Stock ticker.
            interval:    Time interval.
            time_period: Number of data points.
            series_type: "close", "open", "high", "low".

        Returns:
            SMA data dict.
        """
        return self._get(
            function="SMA", symbol=symbol, interval=interval,
            time_period=time_period, series_type=series_type,
        )

    def get_rsi(
        self, symbol: str, interval: str = "daily",
        time_period: int = 14, series_type: str = "close",
    ) -> dict:
        """Get Relative Strength Index (RSI).

        Args:
            symbol:      Stock ticker.
            interval:    Time interval.
            time_period: Number of data points.
            series_type: "close", "open", "high", "low".

        Returns:
            RSI data dict.
        """
        return self._get(
            function="RSI", symbol=symbol, interval=interval,
            time_period=time_period, series_type=series_type,
        )

    # -- internal helpers ------------------------------------------------------

    def _get(self, **params) -> dict:
        params["apikey"] = self.api_key
        resp = self.session.get(_API_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()
        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")
        return data
