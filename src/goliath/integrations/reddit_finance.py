"""
Reddit Finance Integration — trending tickers, sentiment, and discussions from finance subreddits.

SETUP INSTRUCTIONS
==================

1. Go to https://www.reddit.com/prefs/apps and create a "script" application.

2. Note your client_id (under the app name) and client_secret.

3. Add to your .env:
     REDDIT_CLIENT_ID=your-client-id
     REDDIT_CLIENT_SECRET=your-client-secret
     REDDIT_USERNAME=your-reddit-username
     REDDIT_PASSWORD=your-reddit-password

   (Reuses the same Reddit credentials as the main Reddit integration.)

IMPORTANT NOTES
===============
- Uses the Reddit JSON API with OAuth2 authentication.
- Targeted at finance subreddits: r/wallstreetbets, r/stocks, r/investing,
  r/options, r/cryptocurrency, r/StockMarket, r/finance.
- Rate limit: 60 requests/minute with OAuth.
- No separate API key needed — uses existing Reddit credentials.

Usage:
    from goliath.integrations.reddit_finance import RedditFinanceClient

    rf = RedditFinanceClient()

    # Get hot posts from r/wallstreetbets
    posts = rf.get_hot("wallstreetbets", limit=25)

    # Get top posts from r/stocks this week
    top = rf.get_top("stocks", time_filter="week", limit=25)

    # Search for ticker mentions across finance subs
    results = rf.search_ticker("TSLA")

    # Get DD (due diligence) posts
    dd = rf.get_due_diligence("wallstreetbets", limit=10)

    # Get posts mentioning a specific ticker in a subreddit
    mentions = rf.get_ticker_mentions("stocks", "AAPL", limit=20)

    # Get trending discussions from multiple finance subs
    trending = rf.get_trending_finance(limit=50)
"""

import requests

from goliath import config

_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
_API_BASE = "https://oauth.reddit.com"

_FINANCE_SUBS = [
    "wallstreetbets", "stocks", "investing", "options",
    "cryptocurrency", "StockMarket", "finance",
]


class RedditFinanceClient:
    """Reddit Finance client for stock/crypto discussions and sentiment."""

    def __init__(self):
        if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
            raise RuntimeError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required. "
                "Add them to .env. See integrations/reddit_finance.py for setup."
            )

        self._username = config.REDDIT_USERNAME or ""
        self._password = config.REDDIT_PASSWORD or ""
        self._client_id = config.REDDIT_CLIENT_ID
        self._client_secret = config.REDDIT_CLIENT_SECRET

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"GOLIATH:reddit_finance:v1.0 (by /u/{self._username})"
        })

        self._authenticate()

    # -- Subreddit Feeds -------------------------------------------------------

    def get_hot(self, subreddit: str, limit: int = 25) -> list[dict]:
        """Get hot posts from a subreddit.

        Args:
            subreddit: Subreddit name (e.g. "wallstreetbets").
            limit:     Number of posts (max 100).

        Returns:
            List of post dicts.
        """
        return self._get_listing(f"/r/{subreddit}/hot", limit=limit)

    def get_top(
        self, subreddit: str, time_filter: str = "week", limit: int = 25
    ) -> list[dict]:
        """Get top posts from a subreddit.

        Args:
            subreddit:   Subreddit name.
            time_filter: "hour", "day", "week", "month", "year", "all".
            limit:       Number of posts.

        Returns:
            List of post dicts.
        """
        return self._get_listing(
            f"/r/{subreddit}/top", limit=limit, t=time_filter
        )

    def get_new(self, subreddit: str, limit: int = 25) -> list[dict]:
        """Get newest posts from a subreddit.

        Args:
            subreddit: Subreddit name.
            limit:     Number of posts.

        Returns:
            List of post dicts.
        """
        return self._get_listing(f"/r/{subreddit}/new", limit=limit)

    # -- Ticker Search ---------------------------------------------------------

    def search_ticker(
        self, ticker: str, limit: int = 25, time_filter: str = "week"
    ) -> list[dict]:
        """Search for ticker mentions across finance subreddits.

        Args:
            ticker:      Stock/crypto ticker (e.g. "TSLA", "BTC").
            limit:       Max results.
            time_filter: "hour", "day", "week", "month", "year", "all".

        Returns:
            List of post dicts mentioning the ticker.
        """
        subreddits = "+".join(_FINANCE_SUBS)
        return self._get_listing(
            f"/r/{subreddits}/search",
            limit=limit,
            q=f"${ticker} OR {ticker}",
            restrict_sr="on",
            sort="relevance",
            t=time_filter,
        )

    def get_ticker_mentions(
        self, subreddit: str, ticker: str, limit: int = 25
    ) -> list[dict]:
        """Get posts mentioning a specific ticker in a subreddit.

        Args:
            subreddit: Subreddit name.
            ticker:    Stock/crypto ticker.
            limit:     Max results.

        Returns:
            List of post dicts.
        """
        return self._get_listing(
            f"/r/{subreddit}/search",
            limit=limit,
            q=f"${ticker} OR {ticker}",
            restrict_sr="on",
            sort="new",
        )

    # -- Specialized Finance Feeds ---------------------------------------------

    def get_due_diligence(self, subreddit: str, limit: int = 10) -> list[dict]:
        """Get Due Diligence (DD) posts from a subreddit.

        Args:
            subreddit: Subreddit name (e.g. "wallstreetbets").
            limit:     Max results.

        Returns:
            List of DD post dicts.
        """
        return self._get_listing(
            f"/r/{subreddit}/search",
            limit=limit,
            q='flair:"DD" OR flair:"Due Diligence"',
            restrict_sr="on",
            sort="new",
        )

    def get_trending_finance(self, limit: int = 50) -> list[dict]:
        """Get trending posts across all finance subreddits.

        Args:
            limit: Max results.

        Returns:
            List of post dicts from multiple finance subs.
        """
        subreddits = "+".join(_FINANCE_SUBS)
        return self._get_listing(f"/r/{subreddits}/hot", limit=limit)

    # -- internal helpers ------------------------------------------------------

    def _authenticate(self):
        """Obtain OAuth2 access token."""
        data: dict = {"grant_type": "password",
                      "username": self._username,
                      "password": self._password}

        resp = requests.post(
            _OAUTH_URL, data=data,
            auth=(self._client_id, self._client_secret),
            headers=self.session.headers,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token", "")
        if not token:
            raise RuntimeError("Reddit OAuth failed — check credentials.")
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _get_listing(self, path: str, limit: int = 25, **extra) -> list[dict]:
        """Fetch a Reddit listing and extract post data."""
        params: dict = {"limit": limit, "raw_json": 1, **extra}
        resp = self.session.get(f"{_API_BASE}{path}", params=params)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return [
            child["data"]
            for child in data.get("children", [])
            if child.get("kind") == "t3"
        ]
