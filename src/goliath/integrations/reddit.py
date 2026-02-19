"""
Reddit Integration — submit posts, comment, and browse via the Reddit API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.reddit.com/prefs/apps

2. Click "create another app..." at the bottom of the page.
   - Type: choose "script" (for personal/server-side use).
   - Name: e.g. "GOLIATH"
   - Redirect URI: http://localhost:8080 (required but unused for script apps).
   - Click "create app".

3. Note down:
   - Client ID: the string under the app name (e.g. "AbCdEf12345").
   - Client Secret: the "secret" field.

4. Add credentials to your .env:
     REDDIT_CLIENT_ID=AbCdEf12345
     REDDIT_CLIENT_SECRET=your-secret-here
     REDDIT_USERNAME=your-reddit-username
     REDDIT_PASSWORD=your-reddit-password

IMPORTANT NOTES
===============
- Script apps use OAuth2 password grant — suitable for personal or
  server-side automation on your own account.
- Reddit API rules: identify your app via a custom User-Agent,
  and keep requests under 60/minute.
- For production or third-party use, use the "web app" or "installed app"
  type with proper OAuth2 authorization code flow instead.

Usage:
    from goliath.integrations.reddit import RedditClient

    reddit = RedditClient()

    # Submit a text post
    reddit.submit_text("test", title="Hello from GOLIATH", text="Automated post!")

    # Submit a link post
    reddit.submit_link("test", title="Check this out", url="https://example.com")

    # Comment on a post
    reddit.comment("t3_abc123", "Great post!")

    # Get posts from a subreddit
    posts = reddit.get_subreddit_posts("python", sort="hot", limit=10)

    # Vote on a post or comment
    reddit.vote("t3_abc123", direction=1)  # 1=upvote, 0=unvote, -1=downvote
"""

import requests

from goliath import config

_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
_API_BASE = "https://oauth.reddit.com"
_USER_AGENT = "python:goliath-ai:v0.1.0 (by /u/{username})"


class RedditClient:
    """Reddit API client using OAuth2 password grant."""

    def __init__(self):
        creds = {
            "REDDIT_CLIENT_ID": config.REDDIT_CLIENT_ID,
            "REDDIT_CLIENT_SECRET": config.REDDIT_CLIENT_SECRET,
            "REDDIT_USERNAME": config.REDDIT_USERNAME,
            "REDDIT_PASSWORD": config.REDDIT_PASSWORD,
        }
        missing = [k for k, v in creds.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing Reddit credentials: {', '.join(missing)}. "
                "Add them to .env or export as environment variables. "
                "See integrations/reddit.py for setup instructions."
            )

        self._client_id = config.REDDIT_CLIENT_ID
        self._client_secret = config.REDDIT_CLIENT_SECRET
        self._username = config.REDDIT_USERNAME
        self._password = config.REDDIT_PASSWORD
        self._token = None

        self.session = requests.Session()
        self.session.headers["User-Agent"] = _USER_AGENT.format(username=self._username)
        self._authenticate()

    def _authenticate(self):
        """Obtain an OAuth2 access token via password grant."""
        resp = requests.post(
            _OAUTH_URL,
            auth=(self._client_id, self._client_secret),
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
            headers={"User-Agent": _USER_AGENT.format(username=self._username)},
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(
                f"Reddit OAuth failed: {data.get('error', 'unknown')} — "
                f"{data.get('error_description', 'no details')}"
            )

        self._token = data["access_token"]
        self.session.headers["Authorization"] = f"Bearer {self._token}"

    # -- public API --------------------------------------------------------

    def submit_text(self, subreddit: str, title: str, text: str = "") -> dict:
        """Submit a self (text) post to a subreddit.

        Args:
            subreddit: Subreddit name (without r/ prefix).
            title:     Post title.
            text:      Post body (markdown).

        Returns:
            API response dict with the post URL and ID.
        """
        return self._post("/api/submit", data={
            "sr": subreddit,
            "kind": "self",
            "title": title,
            "text": text,
        })

    def submit_link(self, subreddit: str, title: str, url: str) -> dict:
        """Submit a link post to a subreddit.

        Args:
            subreddit: Subreddit name.
            title:     Post title.
            url:       URL to link to.

        Returns:
            API response dict.
        """
        return self._post("/api/submit", data={
            "sr": subreddit,
            "kind": "link",
            "title": title,
            "url": url,
        })

    def comment(self, thing_id: str, text: str) -> dict:
        """Add a top-level comment to a post.

        Args:
            thing_id: Fullname of the post (e.g. "t3_abc123").
            text:     Comment body (markdown).

        Returns:
            API response dict.
        """
        return self._post("/api/comment", data={
            "thing_id": thing_id,
            "text": text,
        })

    def reply(self, thing_id: str, text: str) -> dict:
        """Reply to a comment.

        Args:
            thing_id: Fullname of the comment (e.g. "t1_def456").
            text:     Reply body (markdown).

        Returns:
            API response dict.
        """
        return self._post("/api/comment", data={
            "thing_id": thing_id,
            "text": text,
        })

    def get_subreddit_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
        time: str = "day",
    ) -> list[dict]:
        """Get posts from a subreddit.

        Args:
            subreddit: Subreddit name.
            sort:      Sort order — "hot", "new", "top", "rising".
            limit:     Number of posts (1–100).
            time:      Time filter for "top" sort — "hour", "day", "week", "month", "year", "all".

        Returns:
            List of post data dicts.
        """
        params: dict = {"limit": limit}
        if sort == "top":
            params["t"] = time
        data = self._get(f"/r/{subreddit}/{sort}", params=params)
        return [child["data"] for child in data.get("data", {}).get("children", [])]

    def get_post(self, subreddit: str, post_id: str) -> dict:
        """Get a single post and its comments.

        Args:
            subreddit: Subreddit name.
            post_id:   Post ID (without t3_ prefix).

        Returns:
            Dict with "post" and "comments" keys.
        """
        data = self._get(f"/r/{subreddit}/comments/{post_id}")
        result: dict = {}
        if isinstance(data, list) and len(data) >= 1:
            post_listing = data[0].get("data", {}).get("children", [])
            if post_listing:
                result["post"] = post_listing[0].get("data", {})
        if isinstance(data, list) and len(data) >= 2:
            comment_listing = data[1].get("data", {}).get("children", [])
            result["comments"] = [c.get("data", {}) for c in comment_listing]
        return result

    def get_user(self, username: str) -> dict:
        """Get public info about a Reddit user.

        Args:
            username: Reddit username (without u/ prefix).

        Returns:
            User data dict.
        """
        data = self._get(f"/user/{username}/about")
        return data.get("data", data)

    def vote(self, thing_id: str, direction: int) -> None:
        """Vote on a post or comment.

        Args:
            thing_id:  Fullname (e.g. "t3_abc123" for post, "t1_def456" for comment).
            direction: 1 = upvote, 0 = unvote, -1 = downvote.
        """
        if direction not in (1, 0, -1):
            raise ValueError("direction must be 1, 0, or -1.")
        self._post("/api/vote", data={"id": thing_id, "dir": direction})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs):
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
