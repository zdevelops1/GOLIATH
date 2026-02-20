"""
Medium Integration — publish and manage posts via the Medium API.

SETUP INSTRUCTIONS
==================

1. Log in to Medium at https://medium.com/

2. Go to Settings > Security and applications > Integration tokens
   (or visit https://medium.com/me/settings/security).

3. Enter a description (e.g. "GOLIATH") and click "Get token".

4. Copy the token and add it to your .env:
     MEDIUM_ACCESS_TOKEN=281a7...

IMPORTANT NOTES
===============
- Authentication uses a self-issued integration token (Bearer).
- API docs: https://github.com/Medium/medium-api-docs
- Rate limit: limited to ~100 requests per day.
- The Medium API is limited in scope — primarily for publishing posts.
- Posts can be published as "public", "draft", or "unlisted".
- Content format supports HTML or Markdown.

Usage:
    from goliath.integrations.medium import MediumClient

    med = MediumClient()

    # Get authenticated user info
    me = med.get_me()

    # Publish a post
    post = med.create_post(
        title="My First AI-Generated Article",
        content="# Hello World\\n\\nThis article was published by GOLIATH.",
        content_format="markdown",
        publish_status="draft",
        tags=["ai", "automation"],
    )

    # List publications the user contributes to
    pubs = med.list_publications()

    # Publish to a specific publication
    post = med.create_publication_post(
        publication_id="abc123",
        title="Team Update",
        content="<h1>Weekly Update</h1><p>Progress on all fronts.</p>",
        content_format="html",
    )
"""

import requests

from goliath import config

_API_BASE = "https://api.medium.com/v1"


class MediumClient:
    """Medium API client for publishing and managing posts."""

    def __init__(self):
        if not config.MEDIUM_ACCESS_TOKEN:
            raise RuntimeError(
                "MEDIUM_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/medium.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.MEDIUM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self._user_id: str | None = None

    # -- User --------------------------------------------------------------

    def get_me(self) -> dict:
        """Get the authenticated user's profile.

        Returns:
            User dict with id, username, name, url, and imageUrl.
        """
        return self._get("/me")

    @property
    def user_id(self) -> str:
        """Lazily fetch and cache the authenticated user's ID."""
        if self._user_id is None:
            self._user_id = self.get_me()["id"]
        return self._user_id

    # -- Posts -------------------------------------------------------------

    def create_post(
        self,
        title: str,
        content: str,
        content_format: str = "markdown",
        publish_status: str = "draft",
        tags: list[str] | None = None,
        canonical_url: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a post under the authenticated user.

        Args:
            title:           Post title.
            content:         Post body (HTML or Markdown).
            content_format:  "html" or "markdown".
            publish_status:  "public", "draft", or "unlisted".
            tags:            Up to 5 topic tags.
            canonical_url:   Original URL if cross-posting.
            kwargs:          Additional fields.

        Returns:
            Created post dict with id, title, url, etc.
        """
        data: dict = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "publishStatus": publish_status,
            **kwargs,
        }
        if tags:
            data["tags"] = tags[:5]
        if canonical_url:
            data["canonicalUrl"] = canonical_url

        return self._post(f"/users/{self.user_id}/posts", json=data)

    # -- Publications ------------------------------------------------------

    def list_publications(self) -> list[dict]:
        """List publications the authenticated user contributes to.

        Returns:
            List of publication dicts with id, name, description, url, etc.
        """
        return self._get(f"/users/{self.user_id}/publications")

    def create_publication_post(
        self,
        publication_id: str,
        title: str,
        content: str,
        content_format: str = "markdown",
        publish_status: str = "draft",
        tags: list[str] | None = None,
        canonical_url: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a post under a publication.

        Args:
            publication_id:  Publication ID.
            title:           Post title.
            content:         Post body (HTML or Markdown).
            content_format:  "html" or "markdown".
            publish_status:  "public", "draft", or "unlisted".
            tags:            Up to 5 topic tags.
            canonical_url:   Original URL if cross-posting.
            kwargs:          Additional fields.

        Returns:
            Created post dict.
        """
        data: dict = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "publishStatus": publish_status,
            **kwargs,
        }
        if tags:
            data["tags"] = tags[:5]
        if canonical_url:
            data["canonicalUrl"] = canonical_url

        return self._post(f"/publications/{publication_id}/posts", json=data)

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)
