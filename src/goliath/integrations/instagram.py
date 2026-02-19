"""
Instagram Integration — post photos, videos (Reels), and carousels via Graph API.

SETUP INSTRUCTIONS
==================

1. Create a Meta Developer account at https://developers.facebook.com

2. Create a new app (type: Business) in the Meta App Dashboard.

3. Your Instagram account must be a Business or Creator account
   (switch in Instagram > Settings > Account type).

4. Two authentication paths are available:

   Option A — Facebook Login for Business (traditional):
     - Link your Instagram Business account to a Facebook Page.
     - Request permissions: instagram_basic, instagram_content_publish,
       pages_read_engagement, pages_show_list
     - Base URL: https://graph.facebook.com

   Option B — Instagram Direct Login (newer, no Facebook Page needed):
     - Request permissions: instagram_business_basic,
       instagram_business_content_publish
     - Base URL: https://graph.instagram.com

5. Obtain a User Access Token through the OAuth flow in your app.
   For development/testing, generate one in the Graph API Explorer:
   https://developers.facebook.com/tools/explorer/

6. Get your Instagram User ID:
   GET https://graph.facebook.com/v21.0/me?fields=id&access_token={TOKEN}

7. Add these to your .env file:
     INSTAGRAM_USER_ID=your-ig-user-id
     INSTAGRAM_ACCESS_TOKEN=your-long-lived-token

IMPORTANT NOTES
===============
- Media URLs (image_url, video_url) must be PUBLICLY ACCESSIBLE. Instagram's
  servers fetch them during container creation. Use a CDN, S3 bucket, or any
  public hosting.
- Containers expire after 24 hours if not published.
- Rate limit: 25 published posts per 24-hour rolling window per account.
- Videos/Reels require processing time — the client polls automatically.
- For production use, your app must pass Meta's App Review for the
  content_publish permission.

Usage:
    from goliath.integrations.instagram import InstagramClient

    ig = InstagramClient()

    # Post a photo
    ig.post_image("https://example.com/photo.jpg", caption="Hello from GOLIATH!")

    # Post a Reel
    ig.post_video("https://example.com/clip.mp4", caption="My first Reel")

    # Post a carousel
    ig.post_carousel(
        items=[
            {"image_url": "https://example.com/1.jpg"},
            {"image_url": "https://example.com/2.jpg"},
            {"video_url": "https://example.com/3.mp4"},
        ],
        caption="Swipe through!",
    )
"""

import time

import requests

from goliath import config

_API_VERSION = "v21.0"
_BASE_URL = f"https://graph.facebook.com/{_API_VERSION}"


class InstagramClient:
    """Instagram Graph API client for publishing photos, videos, and carousels."""

    def __init__(self):
        if not config.INSTAGRAM_ACCESS_TOKEN:
            raise RuntimeError(
                "INSTAGRAM_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/instagram.py for full setup instructions."
            )
        if not config.INSTAGRAM_USER_ID:
            raise RuntimeError(
                "INSTAGRAM_USER_ID is not set. "
                "Add it to .env or export as an environment variable."
            )

        self.user_id = config.INSTAGRAM_USER_ID
        self.token = config.INSTAGRAM_ACCESS_TOKEN

    # -- public API --------------------------------------------------------

    def post_image(self, image_url: str, caption: str = "") -> dict:
        """Publish a single image post.

        Args:
            image_url: Publicly accessible URL to a JPEG image.
            caption:   Optional post caption.

        Returns:
            Dict with the published media ID.
        """
        container_id = self._create_container(image_url=image_url, caption=caption)
        return self._publish(container_id)

    def post_video(
        self,
        video_url: str,
        caption: str = "",
        share_to_feed: bool = True,
        cover_url: str | None = None,
    ) -> dict:
        """Publish a video as a Reel.

        Args:
            video_url:     Publicly accessible URL to an MP4 video.
            caption:       Optional post caption.
            share_to_feed: Whether the Reel also appears in the Feed tab.
            cover_url:     Optional publicly accessible URL for a custom cover image.

        Returns:
            Dict with the published media ID.
        """
        params = {
            "video_url": video_url,
            "media_type": "REELS",
            "caption": caption,
            "share_to_feed": str(share_to_feed).lower(),
        }
        if cover_url:
            params["cover_url"] = cover_url

        container_id = self._create_container(**params)
        self._wait_for_processing(container_id)
        return self._publish(container_id)

    def post_carousel(self, items: list[dict], caption: str = "") -> dict:
        """Publish a carousel post (2–10 images and/or videos).

        Args:
            items:   List of dicts, each with either "image_url" or "video_url".
            caption: Optional caption for the carousel.

        Returns:
            Dict with the published media ID.
        """
        if len(items) < 2:
            raise ValueError("Carousels require at least 2 items.")
        if len(items) > 10:
            raise ValueError("Carousels allow a maximum of 10 items.")

        # Create individual item containers
        child_ids = []
        for item in items:
            params = {"is_carousel_item": "true"}
            if "image_url" in item:
                params["image_url"] = item["image_url"]
            elif "video_url" in item:
                params["video_url"] = item["video_url"]
                params["media_type"] = "VIDEO"
            else:
                raise ValueError(
                    "Each carousel item must have 'image_url' or 'video_url'."
                )
            child_ids.append(self._create_container(**params))

        # Wait for any video items to finish processing
        for child_id in child_ids:
            self._wait_for_processing(child_id)

        # Create the carousel container
        carousel_id = self._create_container(
            media_type="CAROUSEL",
            children=",".join(child_ids),
            caption=caption,
        )
        return self._publish(carousel_id)

    # -- internal helpers --------------------------------------------------

    def _create_container(self, **params) -> str:
        """Create a media container and return its ID."""
        resp = requests.post(
            f"{_BASE_URL}/{self.user_id}/media",
            headers={"Authorization": f"Bearer {self.token}"},
            data=params,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _publish(self, container_id: str) -> dict:
        """Publish a media container and return the response."""
        resp = requests.post(
            f"{_BASE_URL}/{self.user_id}/media_publish",
            headers={"Authorization": f"Bearer {self.token}"},
            data={"creation_id": container_id},
        )
        resp.raise_for_status()
        return resp.json()

    def _wait_for_processing(self, container_id: str, timeout: int = 300):
        """Poll a container until processing is finished or timeout is reached."""
        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(
                f"{_BASE_URL}/{container_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"fields": "status_code"},
            )
            resp.raise_for_status()
            status = resp.json().get("status_code")

            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(
                    f"Instagram media processing failed for container {container_id}."
                )
            if status == "EXPIRED":
                raise RuntimeError(
                    f"Instagram container {container_id} expired before publishing."
                )

            # IN_PROGRESS or no status (image) — wait and retry
            time.sleep(10)

        raise TimeoutError(
            f"Instagram media processing timed out after {timeout}s "
            f"for container {container_id}."
        )
