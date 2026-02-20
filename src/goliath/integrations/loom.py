"""
Loom Integration — manage videos, folders, and embeds via the Loom Public API.

SETUP INSTRUCTIONS
==================

1. Log in to Loom at https://www.loom.com/

2. Go to your Workspace Settings > Developer (or visit
   https://www.loom.com/account/developer).

3. Under "Public API", generate a Personal Access Token or create an
   OAuth app for your integration.

4. Add to your .env:
     LOOM_ACCESS_TOKEN=your_access_token_here

IMPORTANT NOTES
===============
- Authentication uses a Bearer token (Developer or OAuth).
- API docs: https://developers.loom.com/docs
- Rate limit: 100 requests per minute.
- The Loom API provides read/manage access to videos, folders, and embeds.
- Video upload is done via the Loom SDK (not the REST API).

Usage:
    from goliath.integrations.loom import LoomClient

    loom = LoomClient()

    # List videos
    videos = loom.list_videos()

    # Get a video
    video = loom.get_video("VIDEO_ID")

    # Update video metadata
    loom.update_video("VIDEO_ID", title="Updated Title")

    # Delete a video
    loom.delete_video("VIDEO_ID")

    # Get video transcript
    transcript = loom.get_transcript("VIDEO_ID")

    # List folders
    folders = loom.list_folders()

    # Get embed info for a Loom URL
    embed = loom.get_oembed("https://www.loom.com/share/abc123")
"""

import requests

from goliath import config

_API_BASE = "https://developer.loom.com/v1"
_OEMBED_URL = "https://www.loom.com/v1/oembed"


class LoomClient:
    """Loom Public API client for videos, folders, and embeds."""

    def __init__(self):
        if not config.LOOM_ACCESS_TOKEN:
            raise RuntimeError(
                "LOOM_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/loom.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.LOOM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })

    # -- Videos ------------------------------------------------------------

    def list_videos(
        self, limit: int = 25, cursor: str | None = None
    ) -> dict:
        """List videos in the workspace.

        Args:
            limit:  Max results per page.
            cursor: Pagination cursor from a previous response.

        Returns:
            Dict with "videos" list and optional "next_cursor".
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._get("/videos", params=params)

    def get_video(self, video_id: str) -> dict:
        """Get a video by ID.

        Args:
            video_id: Loom video ID.

        Returns:
            Video dict with title, description, duration, urls, etc.
        """
        return self._get(f"/videos/{video_id}")

    def update_video(self, video_id: str, **kwargs) -> dict:
        """Update video metadata.

        Args:
            video_id: Loom video ID.
            kwargs:   Fields to update (title, description, privacy, etc.).

        Returns:
            Updated video dict.
        """
        resp = self.session.patch(f"{_API_BASE}/videos/{video_id}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def delete_video(self, video_id: str) -> None:
        """Delete a video.

        Args:
            video_id: Loom video ID.
        """
        resp = self.session.delete(f"{_API_BASE}/videos/{video_id}")
        resp.raise_for_status()

    # -- Transcripts -------------------------------------------------------

    def get_transcript(self, video_id: str) -> dict:
        """Get the transcript for a video.

        Args:
            video_id: Loom video ID.

        Returns:
            Transcript dict with segments and text.
        """
        return self._get(f"/videos/{video_id}/transcript")

    # -- Folders -----------------------------------------------------------

    def list_folders(
        self, limit: int = 25, cursor: str | None = None
    ) -> dict:
        """List folders in the workspace.

        Args:
            limit:  Max results per page.
            cursor: Pagination cursor.

        Returns:
            Dict with "folders" list and optional "next_cursor".
        """
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._get("/folders", params=params)

    def get_folder(self, folder_id: str) -> dict:
        """Get a folder by ID.

        Args:
            folder_id: Folder ID.

        Returns:
            Folder dict.
        """
        return self._get(f"/folders/{folder_id}")

    # -- oEmbed ------------------------------------------------------------

    def get_oembed(self, url: str, maxwidth: int | None = None) -> dict:
        """Get oEmbed data for a Loom share URL.

        Args:
            url:      Loom share URL (e.g. "https://www.loom.com/share/abc123").
            maxwidth: Max embed width in pixels.

        Returns:
            oEmbed response with html, title, thumbnail, etc.
        """
        params: dict = {"url": url}
        if maxwidth:
            params["maxwidth"] = maxwidth
        resp = requests.get(_OEMBED_URL, params=params)
        resp.raise_for_status()
        return resp.json()

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
