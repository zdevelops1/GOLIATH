"""
YouTube Integration — upload videos, manage channels, and retrieve data via the YouTube Data API v3.

SETUP INSTRUCTIONS
==================

1. Go to https://console.cloud.google.com/ and create or select a project.

2. Enable the "YouTube Data API v3" in APIs & Services > Library.

3. Authentication options:

   Option A — API Key (read-only, public data):
     - Go to APIs & Services > Credentials > Create Credentials > API Key.
     - Set YOUTUBE_API_KEY in your .env.

   Option B — OAuth 2.0 (upload, manage your channel):
     - Go to APIs & Services > Credentials > Create Credentials > OAuth client ID.
     - Application type: Desktop app or Web application.
     - Download the client secret JSON (not needed for GOLIATH — use the
       token directly).
     - Generate an access token with scopes:
       youtube.upload, youtube.force-ssl, youtube
     - Set YOUTUBE_ACCESS_TOKEN in your .env.

4. Add to your .env:
     YOUTUBE_API_KEY=your-api-key-here
     YOUTUBE_ACCESS_TOKEN=your-oauth-token-here

IMPORTANT NOTES
===============
- API key is sufficient for read-only operations (search, list videos, channels).
- Upload/update/delete require an OAuth 2.0 access token.
- Quota: YouTube API has a daily quota (default 10,000 units). Uploads cost
  1,600 units each.
- Video uploads use resumable upload protocol for reliability.

Usage:
    from goliath.integrations.youtube import YouTubeClient

    yt = YouTubeClient()

    # Search for videos
    results = yt.search("Python tutorial", max_results=5)

    # Get video details
    video = yt.get_video("dQw4w9WgXcQ")

    # List channel videos
    videos = yt.list_channel_videos("UCxxxxxx", max_results=10)

    # Upload a video (requires OAuth token)
    yt.upload("video.mp4", title="My Video", description="Uploaded via GOLIATH")
"""

from pathlib import Path

import requests

from goliath import config

_API_BASE = "https://www.googleapis.com/youtube/v3"
_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


class YouTubeClient:
    """YouTube Data API v3 client for search, retrieval, and uploads."""

    def __init__(self):
        if not config.YOUTUBE_API_KEY and not config.YOUTUBE_ACCESS_TOKEN:
            raise RuntimeError(
                "Neither YOUTUBE_API_KEY nor YOUTUBE_ACCESS_TOKEN is set. "
                "Add at least one to .env or export as an environment variable. "
                "See integrations/youtube.py for setup instructions."
            )

        self._api_key = config.YOUTUBE_API_KEY
        self._token = config.YOUTUBE_ACCESS_TOKEN
        self.session = requests.Session()
        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"

    # -- public API --------------------------------------------------------

    def search(
        self,
        query: str,
        max_results: int = 5,
        order: str = "relevance",
        video_type: str = "any",
    ) -> list[dict]:
        """Search for videos.

        Args:
            query:       Search query string.
            max_results: Number of results (1–50).
            order:       Sort order — "relevance", "date", "viewCount", "rating".
            video_type:  "any", "episode", or "movie".

        Returns:
            List of search result items.
        """
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "videoType": video_type,
        }
        return self._get("/search", params=params).get("items", [])

    def get_video(self, video_id: str) -> dict:
        """Get detailed information about a video.

        Args:
            video_id: YouTube video ID (e.g. "dQw4w9WgXcQ").

        Returns:
            Video resource dict with snippet, statistics, and content details.
        """
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
        }
        items = self._get("/videos", params=params).get("items", [])
        if not items:
            raise ValueError(f"Video not found: {video_id}")
        return items[0]

    def list_channel_videos(
        self,
        channel_id: str,
        max_results: int = 10,
        order: str = "date",
    ) -> list[dict]:
        """List videos from a channel.

        Args:
            channel_id:  YouTube channel ID.
            max_results: Number of results (1–50).
            order:       Sort order — "date", "viewCount", "relevance".

        Returns:
            List of search result items from the channel.
        """
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "maxResults": max_results,
            "order": order,
        }
        return self._get("/search", params=params).get("items", [])

    def get_channel(self, channel_id: str) -> dict:
        """Get channel details.

        Args:
            channel_id: YouTube channel ID.

        Returns:
            Channel resource dict.
        """
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        }
        items = self._get("/channels", params=params).get("items", [])
        if not items:
            raise ValueError(f"Channel not found: {channel_id}")
        return items[0]

    def get_comments(self, video_id: str, max_results: int = 20) -> list[dict]:
        """Get top-level comments on a video.

        Args:
            video_id:    YouTube video ID.
            max_results: Number of comment threads (1–100).

        Returns:
            List of comment thread items.
        """
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_results,
            "order": "relevance",
        }
        return self._get("/commentThreads", params=params).get("items", [])

    def upload(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        privacy: str = "private",
        category_id: str = "22",
    ) -> dict:
        """Upload a video to YouTube.

        Args:
            file_path:   Path to the video file.
            title:       Video title.
            description: Video description.
            tags:        Optional list of tags.
            privacy:     "private", "unlisted", or "public".
            category_id: YouTube category ID (default "22" = People & Blogs).

        Returns:
            Uploaded video resource dict.
        """
        self._require_token()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
            },
        }

        # Initiate resumable upload
        init_resp = self.session.post(
            _UPLOAD_URL,
            params={"uploadType": "resumable", "part": "snippet,status"},
            json=metadata,
            headers={"X-Upload-Content-Type": "video/*"},
        )
        init_resp.raise_for_status()
        upload_url = init_resp.headers["Location"]

        # Upload the file
        with open(path, "rb") as f:
            upload_resp = self.session.put(
                upload_url,
                data=f,
                headers={"Content-Type": "video/*"},
            )
        upload_resp.raise_for_status()
        return upload_resp.json()

    def update_video(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        privacy: str | None = None,
    ) -> dict:
        """Update video metadata.

        Args:
            video_id:    YouTube video ID.
            title:       New title (None to keep current).
            description: New description (None to keep current).
            tags:        New tags (None to keep current).
            privacy:     New privacy status (None to keep current).

        Returns:
            Updated video resource dict.
        """
        self._require_token()
        body: dict = {"id": video_id}
        parts = []

        snippet: dict = {}
        if title is not None:
            snippet["title"] = title
        if description is not None:
            snippet["description"] = description
        if tags is not None:
            snippet["tags"] = tags
        if snippet:
            body["snippet"] = snippet
            parts.append("snippet")

        if privacy is not None:
            body["status"] = {"privacyStatus": privacy}
            parts.append("status")

        if not parts:
            raise ValueError("No fields to update.")

        resp = self.session.put(
            f"{_API_BASE}/videos",
            params={"part": ",".join(parts)},
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_video(self, video_id: str) -> None:
        """Delete a video from your channel.

        Args:
            video_id: YouTube video ID.
        """
        self._require_token()
        resp = self.session.delete(
            f"{_API_BASE}/videos",
            params={"id": video_id},
        )
        resp.raise_for_status()

    # -- internal helpers --------------------------------------------------

    def _require_token(self):
        """Raise if no OAuth token is configured (needed for write ops)."""
        if not self._token:
            raise RuntimeError(
                "YOUTUBE_ACCESS_TOKEN is required for upload/update/delete. "
                "Set it in .env or export as an environment variable."
            )

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request."""
        params = dict(params or {})
        if not self._token and self._api_key:
            params["key"] = self._api_key
        resp = self.session.get(f"{_API_BASE}{path}", params=params)
        resp.raise_for_status()
        return resp.json()
