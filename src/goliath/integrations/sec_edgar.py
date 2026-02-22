"""
SEC EDGAR Integration — company filings, financial statements, and insider trades via EDGAR.

SETUP INSTRUCTIONS
==================

1. No API key is required — SEC EDGAR is free and public.

2. However, the SEC requires a User-Agent header identifying your application.
   Set in your .env:
     SEC_EDGAR_USER_AGENT=YourName your-email@example.com

   (Format: "Company/App contact-email@example.com")

IMPORTANT NOTES
===============
- API docs: https://www.sec.gov/edgar/searchedgar/companysearch
- EDGAR full-text search: https://efts.sec.gov/LATEST/search-index?q=...
- Company filings: https://data.sec.gov/submissions/CIK{cik}.json
- Rate limit: 10 requests/second (the SEC will throttle/block if exceeded).
- CIK numbers are zero-padded to 10 digits.
- No authentication required but User-Agent is mandatory.

Usage:
    from goliath.integrations.sec_edgar import SECEdgarClient

    sec = SECEdgarClient()

    # Get company filings by ticker
    filings = sec.get_company_filings("AAPL")

    # Get company filings by CIK
    filings = sec.get_filings_by_cik("0000320193")

    # Search EDGAR full-text
    results = sec.search("artificial intelligence", form_type="10-K")

    # Get company facts (XBRL financial data)
    facts = sec.get_company_facts("0000320193")

    # Get specific concept (e.g. Revenue)
    revenue = sec.get_company_concept(
        cik="0000320193",
        taxonomy="us-gaap",
        concept="Revenues",
    )

    # Look up CIK by ticker
    cik = sec.ticker_to_cik("AAPL")

    # Get recent filings feed
    recent = sec.get_recent_filings()
"""

import requests

from goliath import config

_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
_EFTS_BASE = "https://efts.sec.gov/LATEST"
_DATA_BASE = "https://data.sec.gov"
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


class SECEdgarClient:
    """SEC EDGAR client for company filings, financials, and full-text search."""

    def __init__(self):
        user_agent = getattr(config, "SEC_EDGAR_USER_AGENT", "") or ""
        if not user_agent:
            raise RuntimeError(
                "SEC_EDGAR_USER_AGENT is not set. "
                "The SEC requires a User-Agent header. "
                "Add SEC_EDGAR_USER_AGENT='YourName email@example.com' to .env. "
                "See integrations/sec_edgar.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json",
        })

        self._ticker_map: dict | None = None

    # -- Company Filings -------------------------------------------------------

    def get_company_filings(self, ticker: str) -> dict:
        """Get company filings by stock ticker.

        Args:
            ticker: Stock ticker (e.g. "AAPL", "MSFT").

        Returns:
            Filings dict with company info and recent/filing arrays.
        """
        cik = self.ticker_to_cik(ticker)
        return self.get_filings_by_cik(cik)

    def get_filings_by_cik(self, cik: str) -> dict:
        """Get company filings by CIK number.

        Args:
            cik: CIK number (will be zero-padded to 10 digits).

        Returns:
            Filings dict with company info and filing arrays.
        """
        cik_padded = cik.lstrip("0").zfill(10)
        resp = self.session.get(f"{_SUBMISSIONS_BASE}/CIK{cik_padded}.json")
        resp.raise_for_status()
        return resp.json()

    # -- Full-Text Search ------------------------------------------------------

    def search(
        self,
        query: str,
        form_type: str | None = None,
        date_range: str | None = None,
        start: int = 0,
        limit: int = 10,
    ) -> dict:
        """Full-text search across EDGAR filings.

        Args:
            query:      Search query.
            form_type:  Filter by form type ("10-K", "10-Q", "8-K", "S-1", etc.).
            date_range: Date range filter ("custom" with dateStart/dateEnd).
            start:      Starting result index.
            limit:      Number of results (max 100).

        Returns:
            Search results dict with "hits" and metadata.
        """
        params: dict = {"q": query, "from": start, "size": limit}
        if form_type:
            params["forms"] = form_type
        if date_range:
            params["dateRange"] = date_range
        resp = self.session.get(f"{_EFTS_BASE}/search-index", params=params)
        resp.raise_for_status()
        return resp.json()

    # -- XBRL / Company Facts --------------------------------------------------

    def get_company_facts(self, cik: str) -> dict:
        """Get all XBRL financial facts for a company.

        Args:
            cik: CIK number (will be zero-padded).

        Returns:
            Dict with "us-gaap" and "dei" taxonomies containing all reported facts.
        """
        cik_padded = cik.lstrip("0").zfill(10)
        resp = self.session.get(
            f"{_DATA_BASE}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        )
        resp.raise_for_status()
        return resp.json()

    def get_company_concept(
        self,
        cik: str,
        taxonomy: str,
        concept: str,
    ) -> dict:
        """Get a single XBRL concept for a company (e.g. Revenue, Assets).

        Args:
            cik:      CIK number.
            taxonomy: Taxonomy ("us-gaap", "dei", "srt").
            concept:  Concept name (e.g. "Revenues", "Assets", "NetIncomeLoss").

        Returns:
            Dict with units and historical values.
        """
        cik_padded = cik.lstrip("0").zfill(10)
        resp = self.session.get(
            f"{_DATA_BASE}/api/xbrl/companyconcept"
            f"/CIK{cik_padded}/{taxonomy}/{concept}.json"
        )
        resp.raise_for_status()
        return resp.json()

    # -- Ticker Lookup ---------------------------------------------------------

    def ticker_to_cik(self, ticker: str) -> str:
        """Convert a stock ticker to a CIK number.

        Args:
            ticker: Stock ticker (e.g. "AAPL").

        Returns:
            CIK number as a string (zero-padded).

        Raises:
            ValueError: If the ticker is not found.
        """
        if self._ticker_map is None:
            resp = self.session.get(_TICKERS_URL)
            resp.raise_for_status()
            data = resp.json()
            self._ticker_map = {}
            for entry in data.values():
                self._ticker_map[entry["ticker"].upper()] = str(
                    entry["cik_str"]
                )

        cik = self._ticker_map.get(ticker.upper())
        if not cik:
            raise ValueError(
                f"Ticker '{ticker}' not found in SEC EDGAR. "
                "Use a CIK number directly with get_filings_by_cik()."
            )
        return cik

    # -- Recent Filings Feed ---------------------------------------------------

    def get_recent_filings(self, form_type: str | None = None) -> dict:
        """Get the most recent filings from EDGAR.

        Args:
            form_type: Filter by form type (e.g. "10-K").

        Returns:
            Recent filings dict.
        """
        params: dict = {"size": 40}
        if form_type:
            params["forms"] = form_type
        resp = self.session.get(f"{_EFTS_BASE}/search-index", params=params)
        resp.raise_for_status()
        return resp.json()
