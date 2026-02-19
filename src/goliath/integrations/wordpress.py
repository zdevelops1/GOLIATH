"""
WordPress Integration — manage posts, pages, and media via the WordPress REST API.

SETUP INSTRUCTIONS
==================

1. Your WordPress site must have the REST API enabled (enabled by default
   on WordPress 4.7+).

2. For authentication, install and configure one of:

   Option A — Application Passwords (built-in, WordPress 5.6+):
     - Go to Users > Your Profile > Application Passwords.
     - Enter a name (e.g. "GOLIATH") and click "Add New Application Password".
     - Copy the generated password (shown only once).

   Option B — JWT Authentication (plugin):
     - Install the "JWT Authentication for WP REST API" plugin.
     - Generate a token via POST /wp-json/jwt-auth/v1/token.

3. Add to your .env:
     WORDPRESS_URL=https://your-site.com
     WORDPRESS_USERNAME=your-username
     WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

IMPORTANT NOTES
===============
- The base URL should NOT include /wp-json (it's added automatically).
- Application passwords use HTTP Basic Auth (username + app password).
- Rate limits depend on your hosting provider.
- Post status options: "publish", "draft", "pending", "private".
- Media uploads accept images, videos, PDFs, and other common file types.

Usage:
    from goliath.integrations.wordpress import WordPressClient

    wp = WordPressClient()

    # Create a post
    wp.create_post(title="Hello World", content="<p>My first automated post!</p>")

    # List recent posts
    posts = wp.list_posts(per_page=5)

    # Update a post
    wp.update_post(post_id=42, title="Updated Title")

    # Create a page
    wp.create_page(title="About", content="<p>About us page.</p>")
"""

from pathlib import Path

import requests

from goliath import config

_API_PATH = "/wp-json/wp/v2"


class WordPressClient:
    """WordPress REST API client for posts, pages, and media."""

    def __init__(self):
        if not config.WORDPRESS_URL:
            raise RuntimeError(
                "WORDPRESS_URL is not set (e.g. 'https://your-site.com'). "
                "Add it to .env or export as an environment variable."
            )
        if not config.WORDPRESS_USERNAME or not config.WORDPRESS_APP_PASSWORD:
            raise RuntimeError(
                "WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD must be set. "
                "Add them to .env or export as environment variables. "
                "See integrations/wordpress.py for setup instructions."
            )

        self._base = config.WORDPRESS_URL.rstrip("/") + _API_PATH
        self.session = requests.Session()
        self.session.auth = (config.WORDPRESS_USERNAME, config.WORDPRESS_APP_PASSWORD)

    # -- Posts -------------------------------------------------------------

    def list_posts(
        self, per_page: int = 10, page: int = 1, status: str = "publish", **params
    ) -> list[dict]:
        """List posts.

        Args:
            per_page: Number of posts per page (1–100).
            page:     Page number.
            status:   "publish", "draft", "pending", "private", or "any".
            params:   Additional query params (search, categories, tags, etc.).

        Returns:
            List of post resource dicts.
        """
        params.update({"per_page": per_page, "page": page, "status": status})
        return self._get("/posts", params=params)

    def get_post(self, post_id: int) -> dict:
        """Get a post by ID.

        Args:
            post_id: WordPress post ID.

        Returns:
            Post resource dict.
        """
        return self._get(f"/posts/{post_id}")

    def create_post(
        self,
        title: str,
        content: str = "",
        status: str = "draft",
        **kwargs,
    ) -> dict:
        """Create a post.

        Args:
            title:   Post title.
            content: Post content (HTML).
            status:  "publish", "draft", "pending", or "private".
            kwargs:  Additional fields (excerpt, categories, tags, featured_media, etc.).

        Returns:
            Created post resource dict.
        """
        data = {"title": title, "content": content, "status": status, **kwargs}
        return self._post("/posts", json=data)

    def update_post(self, post_id: int, **kwargs) -> dict:
        """Update a post.

        Args:
            post_id: WordPress post ID.
            kwargs:  Fields to update (title, content, status, etc.).

        Returns:
            Updated post resource dict.
        """
        return self._post(f"/posts/{post_id}", json=kwargs)

    def delete_post(self, post_id: int, force: bool = False) -> dict:
        """Delete a post.

        Args:
            post_id: WordPress post ID.
            force:   True to permanently delete (skip trash).

        Returns:
            Deleted post resource dict.
        """
        resp = self.session.delete(
            f"{self._base}/posts/{post_id}", params={"force": force}
        )
        resp.raise_for_status()
        return resp.json()

    # -- Pages -------------------------------------------------------------

    def list_pages(self, per_page: int = 10, page: int = 1, **params) -> list[dict]:
        """List pages.

        Args:
            per_page: Number of pages per page.
            page:     Page number.

        Returns:
            List of page resource dicts.
        """
        params.update({"per_page": per_page, "page": page})
        return self._get("/pages", params=params)

    def create_page(
        self,
        title: str,
        content: str = "",
        status: str = "draft",
        **kwargs,
    ) -> dict:
        """Create a page.

        Args:
            title:   Page title.
            content: Page content (HTML).
            status:  "publish", "draft", "pending", or "private".
            kwargs:  Additional fields (parent, template, etc.).

        Returns:
            Created page resource dict.
        """
        data = {"title": title, "content": content, "status": status, **kwargs}
        return self._post("/pages", json=data)

    def update_page(self, page_id: int, **kwargs) -> dict:
        """Update a page.

        Args:
            page_id: WordPress page ID.
            kwargs:  Fields to update.

        Returns:
            Updated page resource dict.
        """
        return self._post(f"/pages/{page_id}", json=kwargs)

    def delete_page(self, page_id: int, force: bool = False) -> dict:
        """Delete a page.

        Args:
            page_id: WordPress page ID.
            force:   True to permanently delete.

        Returns:
            Deleted page resource dict.
        """
        resp = self.session.delete(
            f"{self._base}/pages/{page_id}", params={"force": force}
        )
        resp.raise_for_status()
        return resp.json()

    # -- Media -------------------------------------------------------------

    def upload_media(self, file_path: str, title: str = "", alt_text: str = "") -> dict:
        """Upload a media file (image, video, PDF, etc.).

        Args:
            file_path: Path to the file.
            title:     Media title.
            alt_text:  Alt text for images.

        Returns:
            Created media resource dict.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        headers = {
            "Content-Disposition": f'attachment; filename="{path.name}"',
        }
        data = {}
        if title:
            data["title"] = title
        if alt_text:
            data["alt_text"] = alt_text

        with open(path, "rb") as f:
            resp = self.session.post(
                f"{self._base}/media",
                headers=headers,
                data=data,
                files={"file": (path.name, f)},
            )
        resp.raise_for_status()
        return resp.json()

    def list_media(self, per_page: int = 10, **params) -> list[dict]:
        """List media items.

        Args:
            per_page: Number of items.
            params:   Additional filters.

        Returns:
            List of media resource dicts.
        """
        params["per_page"] = per_page
        return self._get("/media", params=params)

    # -- Categories --------------------------------------------------------

    def list_categories(self, per_page: int = 100) -> list[dict]:
        """List categories.

        Args:
            per_page: Number of categories.

        Returns:
            List of category resource dicts.
        """
        return self._get("/categories", params={"per_page": per_page})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs):
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
