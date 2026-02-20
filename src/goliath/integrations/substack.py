"""
Substack Integration — manage newsletters, posts, and subscribers via the Substack API.

SETUP INSTRUCTIONS
==================

1. Log in to your Substack publication at https://yourpub.substack.com/

2. Substack does not (as of 2025) offer a public REST API with personal
   access tokens. This integration uses the internal API that the web app
   uses, authenticated with a session cookie.

3. To get your cookie:
   a. Log in to Substack in your browser.
   b. Open DevTools (F12) > Application > Cookies > substack.com.
   c. Copy the value of the "substack.sid" cookie.

4. Add to your .env:
     SUBSTACK_SUBDOMAIN=yourpub
     SUBSTACK_SESSION_COOKIE=s%3Axxxxxxxxx...
     SUBSTACK_USER_ID=12345  (your numeric user ID — find in page source or API)

IMPORTANT NOTES
===============
- This uses the unofficial Substack API; endpoints may change.
- Rate limiting is not publicly documented; be conservative.
- The session cookie expires; you may need to refresh it periodically.
- For publishing, posts are created as drafts and can be published via the UI
  or the publish endpoint.

Usage:
    from goliath.integrations.substack import SubstackClient

    ss = SubstackClient()

    # Create a draft post
    post = ss.create_draft(
        title="Weekly Digest #42",
        subtitle="All the highlights from this week.",
        body_html="<h1>Hello Subscribers</h1><p>Here is your weekly update.</p>",
    )

    # Get a post by ID
    post = ss.get_post(post_id=12345)

    # List published posts
    posts = ss.list_posts(limit=10)

    # Publish a draft
    ss.publish_draft(draft_id=12345)

    # Get publication info
    info = ss.get_publication_info()

    # Get subscriber count
    stats = ss.get_subscriber_stats()
"""

import requests

from goliath import config


class SubstackClient:
    """Substack API client for newsletters, posts, and subscribers."""

    def __init__(self):
        if not config.SUBSTACK_SESSION_COOKIE:
            raise RuntimeError(
                "SUBSTACK_SESSION_COOKIE is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/substack.py for setup instructions."
            )
        if not config.SUBSTACK_SUBDOMAIN:
            raise RuntimeError(
                "SUBSTACK_SUBDOMAIN is not set (e.g. 'yourpub'). "
                "Add it to .env."
            )

        self._base = f"https://{config.SUBSTACK_SUBDOMAIN}.substack.com/api/v1"
        self.user_id = config.SUBSTACK_USER_ID

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        self.session.cookies.set("substack.sid", config.SUBSTACK_SESSION_COOKIE)

    # -- Publication -------------------------------------------------------

    def get_publication_info(self) -> dict:
        """Get publication metadata.

        Returns:
            Publication dict with name, subdomain, description, etc.
        """
        return self._get("/publication")

    def get_subscriber_stats(self) -> dict:
        """Get subscriber statistics.

        Returns:
            Stats dict with subscriber counts.
        """
        return self._get("/publication/stats")

    # -- Posts -------------------------------------------------------------

    def list_posts(self, limit: int = 12, offset: int = 0) -> list[dict]:
        """List published posts.

        Args:
            limit:  Max posts to return.
            offset: Pagination offset.

        Returns:
            List of post dicts.
        """
        return self._get("/posts", params={"limit": limit, "offset": offset})

    def get_post(self, post_id: int | None = None, slug: str | None = None) -> dict:
        """Get a post by ID or slug.

        Args:
            post_id: Post ID.
            slug:    Post URL slug.

        Returns:
            Post dict.
        """
        if post_id:
            return self._get(f"/posts/{post_id}")
        if slug:
            return self._get(f"/posts/{slug}")
        raise ValueError("Provide either post_id or slug.")

    def create_draft(
        self,
        title: str,
        subtitle: str = "",
        body_html: str = "",
        audience: str = "everyone",
        **kwargs,
    ) -> dict:
        """Create a draft post.

        Args:
            title:     Post title.
            subtitle:  Post subtitle.
            body_html: HTML content body.
            audience:  "everyone", "only_paid", or "founding".
            kwargs:    Additional fields (section_id, etc.).

        Returns:
            Created draft dict with id.
        """
        data: dict = {
            "title": title,
            "subtitle": subtitle,
            "body": {"html": body_html},
            "audience": audience,
            "draft": True,
            "type": "newsletter",
            **kwargs,
        }
        return self._post("/drafts", json=data)

    def update_draft(self, draft_id: int, **kwargs) -> dict:
        """Update a draft post.

        Args:
            draft_id: Draft post ID.
            kwargs:   Fields to update (title, subtitle, body, etc.).

        Returns:
            Updated draft dict.
        """
        resp = self.session.put(f"{self._base}/drafts/{draft_id}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def publish_draft(self, draft_id: int, send_email: bool = True) -> dict:
        """Publish a draft.

        Args:
            draft_id:   Draft post ID.
            send_email: Whether to send the newsletter email.

        Returns:
            Published post dict.
        """
        return self._post(
            f"/drafts/{draft_id}/publish",
            json={"send": send_email},
        )

    def delete_draft(self, draft_id: int) -> None:
        """Delete a draft.

        Args:
            draft_id: Draft post ID.
        """
        resp = self.session.delete(f"{self._base}/drafts/{draft_id}")
        resp.raise_for_status()

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
