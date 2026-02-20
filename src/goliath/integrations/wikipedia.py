"""
Wikipedia Integration — search, read, and summarize Wikipedia articles via the Wikimedia REST API.

SETUP INSTRUCTIONS
==================

No API key is required for basic access to the Wikipedia API.

For higher rate limits or access to the Wikimedia Enterprise API,
set an optional access token:

    WIKIPEDIA_ACCESS_TOKEN=your_token_here  (optional)

For polite use, set a custom User-Agent:

    WIKIPEDIA_USER_AGENT=GOLIATH/1.0 (your@email.com)  (optional)

IMPORTANT NOTES
===============
- The Wikimedia REST API is free and requires no authentication.
- API docs: https://en.wikipedia.org/api/rest_v1/
- Rate limit: 200 requests/second for authenticated users, be polite otherwise.
- Results are from English Wikipedia by default; change the language param for others.
- The API returns HTML content; this client extracts plain text.

Usage:
    from goliath.integrations.wikipedia import WikipediaClient

    wiki = WikipediaClient()

    # Search for articles
    results = wiki.search("artificial intelligence")

    # Get an article summary
    summary = wiki.get_summary("Python_(programming_language)")

    # Get the full article content
    article = wiki.get_article("Python_(programming_language)")

    # Get a random article summary
    random = wiki.random_summary()

    # Get article in another language
    summary = wiki.get_summary("Intelligence_artificielle", language="fr")

    # Search with a limit
    results = wiki.search("quantum computing", limit=5)
"""

import requests

from goliath import config


class WikipediaClient:
    """Wikimedia REST API client for searching and reading Wikipedia articles."""

    def __init__(self, language: str = "en"):
        self.language = language
        self._base = f"https://{language}.wikipedia.org/api/rest_v1"

        self.session = requests.Session()
        ua = getattr(config, "WIKIPEDIA_USER_AGENT", "") or "GOLIATH/1.0"
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "application/json",
        })

        token = getattr(config, "WIKIPEDIA_ACCESS_TOKEN", "")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    # -- Search ------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search Wikipedia articles.

        Args:
            query: Search query.
            limit: Max results (max 100).

        Returns:
            List of result dicts with title, description, and thumbnail.
        """
        params = {"q": query, "limit": limit}
        data = self._get("/search/page", params=params)
        return data.get("pages", [])

    # -- Summaries ---------------------------------------------------------

    def get_summary(self, title: str, language: str | None = None) -> dict:
        """Get a summary of a Wikipedia article.

        Args:
            title:    Article title (use underscores for spaces).
            language: Override language (e.g. "fr", "de", "es").

        Returns:
            Summary dict with title, extract (plain text), description,
            thumbnail, coordinates, etc.
        """
        base = self._base
        if language:
            base = f"https://{language}.wikipedia.org/api/rest_v1"
        resp = self.session.get(f"{base}/page/summary/{title}")
        resp.raise_for_status()
        return resp.json()

    def random_summary(self) -> dict:
        """Get a random article summary.

        Returns:
            Summary dict for a random article.
        """
        resp = self.session.get(f"{self._base}/page/random/summary")
        resp.raise_for_status()
        return resp.json()

    # -- Full Articles -----------------------------------------------------

    def get_article(self, title: str) -> dict:
        """Get the full mobile-formatted article content.

        Args:
            title: Article title.

        Returns:
            Article dict with sections and lead content.
        """
        return self._get(f"/page/mobile-sections/{title}")

    def get_article_html(self, title: str) -> str:
        """Get the full article as HTML.

        Args:
            title: Article title.

        Returns:
            HTML string of the full article.
        """
        resp = self.session.get(
            f"{self._base}/page/html/{title}",
            headers={"Accept": "text/html"},
        )
        resp.raise_for_status()
        return resp.text

    # -- Related & Links ---------------------------------------------------

    def get_related(self, title: str) -> list[dict]:
        """Get related articles.

        Args:
            title: Article title.

        Returns:
            List of related article summary dicts.
        """
        data = self._get(f"/page/related/{title}")
        return data.get("pages", [])

    def get_media(self, title: str) -> list[dict]:
        """Get media files (images, audio, video) used in an article.

        Args:
            title: Article title.

        Returns:
            List of media item dicts.
        """
        data = self._get(f"/page/media-list/{title}")
        return data.get("items", [])

    # -- On This Day -------------------------------------------------------

    def on_this_day(self, month: int, day: int, type: str = "all") -> list[dict]:
        """Get historical events for a date.

        Args:
            month: Month (1–12).
            day:   Day (1–31).
            type:  "all", "selected", "births", "deaths", "events", "holidays".

        Returns:
            List of event dicts.
        """
        path = f"/feed/onthisday/{type}/{month:02d}/{day:02d}"
        data = self._get(path)
        return data.get(type if type != "all" else "selected", data.get("events", []))

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
