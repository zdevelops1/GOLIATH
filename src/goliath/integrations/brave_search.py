"""
Brave Search Integration — run web, news, and image searches via the Brave Search API.

SETUP INSTRUCTIONS
==================

1. Go to https://brave.com/search/api/ and sign up for an API plan.

2. After signing up, go to your dashboard and copy your API key.

3. Add to your .env:
     BRAVE_SEARCH_API_KEY=BSAxxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses a subscription token in the X-Subscription-Token header.
- API docs: https://api.search.brave.com/app/#/documentation
- Free tier: 2000 queries per month.
- Supports web search, news search, image search, and summarization.
- Results include organic results, knowledge graph, FAQ, videos, etc.

Usage:
    from goliath.integrations.brave_search import BraveSearchClient

    bs = BraveSearchClient()

    # Web search
    results = bs.web_search("Python asyncio tutorial")

    # Web search with filters
    results = bs.web_search("climate change", count=5, freshness="pd")

    # News search
    news = bs.news_search("AI regulation 2025")

    # Image search
    images = bs.image_search("aurora borealis")

    # Get a summarized answer
    summary = bs.summarize("What causes the northern lights?")
"""

import requests

from goliath import config

_API_BASE = "https://api.search.brave.com/res/v1"


class BraveSearchClient:
    """Brave Search API client for web, news, and image searches."""

    def __init__(self):
        if not config.BRAVE_SEARCH_API_KEY:
            raise RuntimeError(
                "BRAVE_SEARCH_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/brave_search.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-Subscription-Token": config.BRAVE_SEARCH_API_KEY,
            "Accept": "application/json",
        })

    # -- Web Search --------------------------------------------------------

    def web_search(
        self,
        query: str,
        count: int = 10,
        offset: int = 0,
        country: str | None = None,
        search_lang: str | None = None,
        freshness: str | None = None,
        safesearch: str = "moderate",
        **kwargs,
    ) -> dict:
        """Run a web search.

        Args:
            query:       Search query.
            count:       Number of results (max 20).
            offset:      Pagination offset.
            country:     Country code (e.g. "US", "GB").
            search_lang: Language code (e.g. "en", "fr").
            freshness:   Recency filter ("pd"=day, "pw"=week, "pm"=month, "py"=year).
            safesearch:  "off", "moderate", or "strict".
            kwargs:      Additional params.

        Returns:
            Full search result dict with "web", "faq", "videos", "news",
            "knowledge_graph", etc.
        """
        params: dict = {
            "q": query,
            "count": count,
            "offset": offset,
            "safesearch": safesearch,
            **kwargs,
        }
        if country:
            params["country"] = country
        if search_lang:
            params["search_lang"] = search_lang
        if freshness:
            params["freshness"] = freshness

        return self._get("/web/search", params=params)

    # -- News Search -------------------------------------------------------

    def news_search(
        self,
        query: str,
        count: int = 10,
        freshness: str | None = None,
        **kwargs,
    ) -> list[dict]:
        """Search news articles.

        Args:
            query:     Search query.
            count:     Number of results (max 20).
            freshness: Recency filter ("pd", "pw", "pm").
            kwargs:    Additional params.

        Returns:
            List of news result dicts.
        """
        params: dict = {"q": query, "count": count, **kwargs}
        if freshness:
            params["freshness"] = freshness
        data = self._get("/news/search", params=params)
        return data.get("results", [])

    # -- Image Search ------------------------------------------------------

    def image_search(
        self,
        query: str,
        count: int = 10,
        safesearch: str = "moderate",
        **kwargs,
    ) -> list[dict]:
        """Search images.

        Args:
            query:      Search query.
            count:      Number of results (max 20).
            safesearch: "off", "moderate", or "strict".
            kwargs:     Additional params.

        Returns:
            List of image result dicts with urls, dimensions, etc.
        """
        params: dict = {
            "q": query,
            "count": count,
            "safesearch": safesearch,
            **kwargs,
        }
        data = self._get("/images/search", params=params)
        return data.get("results", [])

    # -- Summarize ---------------------------------------------------------

    def summarize(self, query: str) -> str:
        """Get an AI-summarized answer for a query.

        Args:
            query: Search query.

        Returns:
            Summary answer string.
        """
        data = self._get("/summarizer/search", params={"q": query, "summary": 1})
        return data.get("summary", [{}])[0].get("data", "") if data.get("summary") else ""

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
