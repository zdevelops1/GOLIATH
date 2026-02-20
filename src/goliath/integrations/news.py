"""
News API Integration — search headlines, articles, and sources via NewsAPI.org.

SETUP INSTRUCTIONS
==================

1. Go to https://newsapi.org/ and create a free account.

2. Copy your API key from the dashboard.

3. Add to your .env:
     NEWS_API_KEY=your_api_key_here

IMPORTANT NOTES
===============
- Free tier: 100 requests/day, articles up to 1 month old.
- Paid plans unlock unlimited requests, real-time articles, and commercial use.
- API docs: https://newsapi.org/docs
- Supports filtering by source, language, country, category, and date range.
- Top headlines endpoint covers breaking news; everything endpoint covers all articles.

Usage:
    from goliath.integrations.news import NewsClient

    n = NewsClient()

    # Top headlines by country
    headlines = n.top_headlines(country="us")

    # Top headlines by category
    tech = n.top_headlines(category="technology", country="us")

    # Search all articles
    articles = n.search("artificial intelligence", sort_by="relevancy")

    # Search with date range
    articles = n.search("climate change", from_date="2025-01-01", to_date="2025-01-31")

    # Get available sources
    sources = n.get_sources(language="en")

    # Top headlines from specific sources
    headlines = n.top_headlines(sources="bbc-news,cnn")
"""

import requests

from goliath import config

_API_BASE = "https://newsapi.org/v2"


class NewsClient:
    """NewsAPI client for searching news headlines, articles, and sources."""

    def __init__(self):
        if not config.NEWS_API_KEY:
            raise RuntimeError(
                "NEWS_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/news.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": config.NEWS_API_KEY,
            "Accept": "application/json",
        })

    # -- Top Headlines -----------------------------------------------------

    def top_headlines(
        self,
        country: str | None = None,
        category: str | None = None,
        sources: str | None = None,
        query: str | None = None,
        page_size: int = 20,
        page: int = 1,
    ) -> dict:
        """Get top headlines.

        Args:
            country:   ISO country code (e.g. "us", "gb"). Cannot combine with sources.
            category:  Category ("business", "entertainment", "general", "health",
                       "science", "sports", "technology"). Cannot combine with sources.
            sources:   Comma-separated source IDs (e.g. "bbc-news,cnn").
            query:     Keywords to filter headlines.
            page_size: Number of results per page (max 100).
            page:      Page number.

        Returns:
            Dict with "status", "totalResults", and "articles" list.
        """
        params: dict = {"pageSize": page_size, "page": page}
        if country:
            params["country"] = country
        if category:
            params["category"] = category
        if sources:
            params["sources"] = sources
        if query:
            params["q"] = query
        return self._get("/top-headlines", params=params)

    # -- Everything (Search) -----------------------------------------------

    def search(
        self,
        query: str,
        sources: str | None = None,
        domains: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        page: int = 1,
    ) -> dict:
        """Search all articles.

        Args:
            query:     Search keywords or phrase.
            sources:   Comma-separated source IDs.
            domains:   Comma-separated domains (e.g. "bbc.co.uk,techcrunch.com").
            from_date: Oldest article date (ISO format: "2025-01-01").
            to_date:   Newest article date (ISO format).
            language:  Language code (e.g. "en", "es", "fr").
            sort_by:   "relevancy", "popularity", or "publishedAt".
            page_size: Number of results per page (max 100).
            page:      Page number.

        Returns:
            Dict with "status", "totalResults", and "articles" list.
        """
        params: dict = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
        }
        if sources:
            params["sources"] = sources
        if domains:
            params["domains"] = domains
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._get("/everything", params=params)

    # -- Sources -----------------------------------------------------------

    def get_sources(
        self,
        category: str | None = None,
        language: str | None = None,
        country: str | None = None,
    ) -> list[dict]:
        """Get available news sources.

        Args:
            category: Filter by category.
            language: Filter by language code.
            country:  Filter by country code.

        Returns:
            List of source dicts with id, name, description, url, etc.
        """
        params: dict = {}
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country
        data = self._get("/top-headlines/sources", params=params)
        return data.get("sources", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
