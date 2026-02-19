"""
TikTok Integration — publish videos and manage content via the TikTok Content Posting API.

SETUP INSTRUCTIONS
==================

1. Go to https://developers.tiktok.com/ and create a developer account.

2. Create an app in the TikTok Developer Portal.

3. Apply for the following scopes under "Manage apps":
   - video.publish — post videos
   - video.upload — upload video files
   - video.list — list your videos
   - user.info.basic — read user profile

4. Complete the OAuth 2.0 flow to get an access token:
   - Authorization URL: https://www.tiktok.com/v2/auth/authorize/
   - Token URL: https://open.tiktokapis.com/v2/oauth/token/

5. Add to your .env:
     TIKTOK_ACCESS_TOKEN=your-access-token

IMPORTANT NOTES
===============
- TikTok uses the Content Posting API (v2) for video uploads.
- Videos must be uploaded as files or from publicly accessible URLs.
- Access tokens expire after 24 hours. Use refresh tokens for production.
- Video processing is async — poll the publish status after initiating.
- Maximum video length: 10 minutes. Minimum: 3 seconds.

Usage:
    from goliath.integrations.tiktok import TikTokClient

    tt = TikTokClient()

    # Get user info
    info = tt.get_user_info()

    # List your videos
    videos = tt.list_videos()

    # Upload a video from URL
    tt.publish_video_from_url(
        video_url="https://example.com/video.mp4",
        title="My TikTok via GOLIATH",
    )
"""

import requests

from goliath import config

_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokClient:
    """TikTok Content Posting API client for video publishing and management."""

    def __init__(self):
        if not config.TIKTOK_ACCESS_TOKEN:
            raise RuntimeError(
                "TIKTOK_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/tiktok.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {config.TIKTOK_ACCESS_TOKEN}"

    # -- User --------------------------------------------------------------

    def get_user_info(self) -> dict:
        """Get the authenticated user's profile info.

        Returns:
            User data dict with display_name, avatar, follower count, etc.
        """
        resp = self.session.get(
            f"{_API_BASE}/user/info/",
            params={
                "fields": "display_name,avatar_url,follower_count,following_count,likes_count,video_count"
            },
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("user", {})

    # -- Videos ------------------------------------------------------------

    def list_videos(self, max_count: int = 20, cursor: int | None = None) -> dict:
        """List the authenticated user's videos.

        Args:
            max_count: Number of videos (1–20).
            cursor:    Pagination cursor from previous response.

        Returns:
            Dict with "videos" list and optional "cursor" for pagination.
        """
        body: dict = {"max_count": max_count}
        if cursor is not None:
            body["cursor"] = cursor

        resp = self.session.post(
            f"{_API_BASE}/video/list/",
            params={
                "fields": "id,title,create_time,cover_image_url,duration,view_count,like_count,comment_count,share_count"
            },
            json=body,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def query_videos(self, video_ids: list[str]) -> list[dict]:
        """Get details about specific videos by their IDs.

        Args:
            video_ids: List of TikTok video IDs.

        Returns:
            List of video data dicts.
        """
        resp = self.session.post(
            f"{_API_BASE}/video/query/",
            params={
                "fields": "id,title,create_time,cover_image_url,duration,view_count,like_count,comment_count,share_count"
            },
            json={"filters": {"video_ids": video_ids}},
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("videos", [])

    def publish_video_from_url(
        self,
        video_url: str,
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
    ) -> dict:
        """Publish a video from a publicly accessible URL.

        Args:
            video_url:       Public URL to the video file.
            title:           Video caption/title (max 2,200 characters).
            privacy_level:   "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS",
                             "FOLLOWER_OF_CREATOR", or "SELF_ONLY".
            disable_comment: Disable comments on the video.
            disable_duet:    Disable duets.
            disable_stitch:  Disable stitches.

        Returns:
            Publish status dict with publish_id for tracking.
        """
        body = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_comment": disable_comment,
                "disable_duet": disable_duet,
                "disable_stitch": disable_stitch,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }

        resp = self.session.post(
            f"{_API_BASE}/post/publish/video/init/",
            json=body,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_publish_status(self, publish_id: str) -> dict:
        """Check the status of a video publish.

        Args:
            publish_id: Publish ID returned from publish_video_from_url.

        Returns:
            Status dict with upload_status and publish details.
        """
        resp = self.session.post(
            f"{_API_BASE}/post/publish/status/fetch/",
            json={"publish_id": publish_id},
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    # -- Comments ----------------------------------------------------------

    def get_comments(
        self, video_id: str, max_count: int = 20, cursor: int | None = None
    ) -> dict:
        """Get comments on a video.

        Args:
            video_id:  TikTok video ID.
            max_count: Number of comments (1–50).
            cursor:    Pagination cursor.

        Returns:
            Dict with "comments" list and optional "cursor".
        """
        body: dict = {"video_id": video_id, "max_count": max_count}
        if cursor is not None:
            body["cursor"] = cursor

        resp = self.session.post(
            f"{_API_BASE}/comment/list/",
            params={"fields": "id,text,create_time,like_count"},
            json=body,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
