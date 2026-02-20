"""
Beehiiv Integration — manage publications, posts, and subscribers via the Beehiiv API.

SETUP INSTRUCTIONS
==================

1. Log in to Beehiiv at https://app.beehiiv.com/

2. Go to Settings > Integrations > API (or visit your publication settings).

3. Generate an API key. You will also need your Publication ID, which is
   visible in the URL when viewing your publication dashboard.

4. Add to your .env:
     BEEHIIV_API_KEY=your_api_key_here
     BEEHIIV_PUBLICATION_ID=pub_xxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses an API key in the Authorization header.
- API docs: https://developers.beehiiv.com/docs/v2
- Rate limit: 5 requests per second.
- The API is centered around a single publication.
- Posts can be created as drafts or scheduled for later.

Usage:
    from goliath.integrations.beehiiv import BeehiivClient

    bh = BeehiivClient()

    # List posts
    posts = bh.list_posts()

    # Get a post
    post = bh.get_post("post_id")

    # Create a post (draft)
    post = bh.create_post(
        title="Weekly Newsletter #10",
        subtitle="All the highlights from this week.",
        content_html="<h1>Hello!</h1><p>Welcome to the newsletter.</p>",
    )

    # List subscribers
    subs = bh.list_subscribers()

    # Create a subscriber
    bh.create_subscriber(email="reader@example.com")

    # Get subscriber by ID
    sub = bh.get_subscriber("sub_id")

    # Get publication stats
    stats = bh.get_publication()
"""

import requests

from goliath import config

_API_BASE = "https://api.beehiiv.com/v2"


class BeehiivClient:
    """Beehiiv API client for publications, posts, and subscribers."""

    def __init__(self):
        if not config.BEEHIIV_API_KEY:
            raise RuntimeError(
                "BEEHIIV_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/beehiiv.py for setup instructions."
            )
        if not config.BEEHIIV_PUBLICATION_ID:
            raise RuntimeError(
                "BEEHIIV_PUBLICATION_ID is not set. "
                "Add it to .env (e.g. 'pub_xxxxxxxx')."
            )

        self.publication_id = config.BEEHIIV_PUBLICATION_ID
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.BEEHIIV_API_KEY}",
            "Content-Type": "application/json",
        })

    # -- Publication -------------------------------------------------------

    def get_publication(self) -> dict:
        """Get publication details.

        Returns:
            Publication dict with name, description, stats, etc.
        """
        return self._get(f"/publications/{self.publication_id}").get("data", {})

    # -- Posts -------------------------------------------------------------

    def list_posts(
        self, status: str | None = None, limit: int = 10, page: int = 1
    ) -> list[dict]:
        """List posts in the publication.

        Args:
            status: Filter by status ("draft", "confirmed", "archived").
            limit:  Results per page.
            page:   Page number.

        Returns:
            List of post dicts.
        """
        params: dict = {"limit": limit, "page": page}
        if status:
            params["status"] = status
        return self._get(
            f"/publications/{self.publication_id}/posts", params=params
        ).get("data", [])

    def get_post(self, post_id: str) -> dict:
        """Get a post by ID.

        Args:
            post_id: Post ID.

        Returns:
            Post dict.
        """
        return self._get(
            f"/publications/{self.publication_id}/posts/{post_id}"
        ).get("data", {})

    def create_post(
        self,
        title: str,
        subtitle: str = "",
        content_html: str = "",
        status: str = "draft",
        **kwargs,
    ) -> dict:
        """Create a post.

        Args:
            title:        Post title.
            subtitle:     Post subtitle.
            content_html: HTML content body.
            status:       "draft" or "confirmed" (published).
            kwargs:       Additional fields (send_at, segment_ids, etc.).

        Returns:
            Created post dict.
        """
        data: dict = {
            "title": title,
            "subtitle": subtitle,
            "content": [{"type": "html", "html": content_html}],
            "status": status,
            **kwargs,
        }
        return self._post(
            f"/publications/{self.publication_id}/posts", json=data
        ).get("data", {})

    def delete_post(self, post_id: str) -> None:
        """Delete a post.

        Args:
            post_id: Post ID.
        """
        resp = self.session.delete(
            f"{_API_BASE}/publications/{self.publication_id}/posts/{post_id}"
        )
        resp.raise_for_status()

    # -- Subscribers -------------------------------------------------------

    def list_subscribers(
        self, status: str | None = None, limit: int = 10, page: int = 1
    ) -> list[dict]:
        """List subscribers.

        Args:
            status: Filter ("active", "inactive", "validating").
            limit:  Results per page.
            page:   Page number.

        Returns:
            List of subscriber dicts.
        """
        params: dict = {"limit": limit, "page": page}
        if status:
            params["status"] = status
        return self._get(
            f"/publications/{self.publication_id}/subscriptions", params=params
        ).get("data", [])

    def get_subscriber(self, subscriber_id: str) -> dict:
        """Get a subscriber by ID.

        Args:
            subscriber_id: Subscriber/subscription ID.

        Returns:
            Subscriber dict.
        """
        return self._get(
            f"/publications/{self.publication_id}/subscriptions/{subscriber_id}"
        ).get("data", {})

    def create_subscriber(
        self,
        email: str,
        utm_source: str = "goliath",
        reactivate: bool = True,
        **kwargs,
    ) -> dict:
        """Create a subscriber.

        Args:
            email:      Subscriber email.
            utm_source: Attribution source.
            reactivate: Whether to reactivate if previously unsubscribed.
            kwargs:     Additional fields (custom_fields, tags, etc.).

        Returns:
            Created subscriber dict.
        """
        data: dict = {
            "email": email,
            "utm_source": utm_source,
            "reactivate_existing": reactivate,
            **kwargs,
        }
        return self._post(
            f"/publications/{self.publication_id}/subscriptions", json=data
        ).get("data", {})

    def update_subscriber(self, subscriber_id: str, **kwargs) -> dict:
        """Update a subscriber.

        Args:
            subscriber_id: Subscriber ID.
            kwargs:        Fields to update (custom_fields, tags, etc.).

        Returns:
            Updated subscriber dict.
        """
        resp = self.session.patch(
            f"{_API_BASE}/publications/{self.publication_id}/subscriptions/{subscriber_id}",
            json=kwargs,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
