"""
X / Twitter Integration — post tweets, threads, and media via API v2.

Uses OAuth 1.0a (User Context) for all write operations.
Requires four credentials set in .env or environment variables:
    X_CONSUMER_KEY, X_CONSUMER_SECRET,
    X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

Usage:
    from goliath.integrations.x import XClient

    x = XClient()
    x.tweet("Hello from GOLIATH!")
    x.thread(["First tweet", "Second tweet", "Third tweet"])
    x.tweet("Check this out!", media_paths=["photo.jpg"])
"""

import math
import time
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

from goliath import config

# --- API endpoints (v2) ---
_TWEETS_URL = "https://api.x.com/2/tweets"
_MEDIA_UPLOAD_URL = "https://api.x.com/2/media/upload"
_MEDIA_INIT_URL = "https://api.x.com/2/media/upload/initialize"

# Files under this size use simple upload; larger ones use chunked.
_SIMPLE_UPLOAD_LIMIT = 1_000_000  # 1 MB

# MIME types for media_category mapping
_MEDIA_CATEGORIES = {
    ".jpg": ("image/jpeg", "tweet_image"),
    ".jpeg": ("image/jpeg", "tweet_image"),
    ".png": ("image/png", "tweet_image"),
    ".webp": ("image/webp", "tweet_image"),
    ".gif": ("image/gif", "tweet_gif"),
    ".mp4": ("video/mp4", "tweet_video"),
}


class XClient:
    """X / Twitter API v2 client for posting tweets, threads, and media."""

    def __init__(self):
        keys = {
            "X_CONSUMER_KEY": config.X_CONSUMER_KEY,
            "X_CONSUMER_SECRET": config.X_CONSUMER_SECRET,
            "X_ACCESS_TOKEN": config.X_ACCESS_TOKEN,
            "X_ACCESS_TOKEN_SECRET": config.X_ACCESS_TOKEN_SECRET,
        }
        missing = [k for k, v in keys.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing X/Twitter credentials: {', '.join(missing)}. "
                "Add them to .env or export as environment variables."
            )

        self.auth = OAuth1(
            keys["X_CONSUMER_KEY"],
            keys["X_CONSUMER_SECRET"],
            keys["X_ACCESS_TOKEN"],
            keys["X_ACCESS_TOKEN_SECRET"],
        )

    # -- public API --------------------------------------------------------

    def tweet(
        self,
        text: str,
        media_paths: list[str] | None = None,
        reply_to: str | None = None,
    ) -> dict:
        """Post a single tweet. Returns the API response data.

        Args:
            text:        Tweet body (up to 280 characters).
            media_paths: Optional list of file paths to attach (max 4 images or 1 video).
            reply_to:    Optional tweet ID to reply to.
        """
        payload: dict = {"text": text}

        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}

        if media_paths:
            media_ids = [self.upload_media(p) for p in media_paths]
            payload["media"] = {"media_ids": media_ids}

        resp = requests.post(
            _TWEETS_URL,
            auth=self.auth,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["data"]

    def thread(
        self,
        tweets: list[str | dict],
    ) -> list[dict]:
        """Post a thread (sequence of connected tweets).

        Each item can be a plain string or a dict with keys:
            {"text": "...", "media_paths": ["..."]}

        Returns a list of API response dicts, one per tweet.
        """
        if not tweets:
            raise ValueError("Thread must contain at least one tweet.")

        results = []
        reply_to = None

        for item in tweets:
            if isinstance(item, str):
                text, media_paths = item, None
            else:
                text = item["text"]
                media_paths = item.get("media_paths")

            data = self.tweet(text, media_paths=media_paths, reply_to=reply_to)
            results.append(data)
            reply_to = data["id"]

        return results

    def upload_media(self, file_path: str) -> str:
        """Upload a media file and return its media ID string."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in _MEDIA_CATEGORIES:
            supported = ", ".join(_MEDIA_CATEGORIES)
            raise ValueError(
                f"Unsupported file type '{suffix}'. Supported: {supported}"
            )

        file_size = path.stat().st_size
        mime_type, media_category = _MEDIA_CATEGORIES[suffix]

        if file_size <= _SIMPLE_UPLOAD_LIMIT and media_category == "tweet_image":
            return self._simple_upload(path)
        else:
            return self._chunked_upload(path, mime_type, media_category, file_size)

    # -- internal helpers --------------------------------------------------

    def _simple_upload(self, path: Path) -> str:
        """Upload a small image via the simple upload endpoint."""
        with open(path, "rb") as f:
            resp = requests.post(
                _MEDIA_UPLOAD_URL,
                auth=self.auth,
                files={"media": (path.name, f)},
            )
        resp.raise_for_status()
        return resp.json()["data"]["id"]

    def _chunked_upload(
        self,
        path: Path,
        mime_type: str,
        media_category: str,
        file_size: int,
    ) -> str:
        """Upload media via the chunked upload flow (INIT → APPEND → FINALIZE)."""
        chunk_size = 1_000_000  # 1 MB per chunk

        # INIT
        init_resp = requests.post(
            _MEDIA_INIT_URL,
            auth=self.auth,
            json={
                "media_type": mime_type,
                "total_bytes": file_size,
                "media_category": media_category,
            },
        )
        init_resp.raise_for_status()
        media_id = init_resp.json()["id"]

        # APPEND
        append_url = f"https://api.x.com/2/media/upload/{media_id}/append"
        total_chunks = math.ceil(file_size / chunk_size)

        with open(path, "rb") as f:
            for segment in range(total_chunks):
                chunk = f.read(chunk_size)
                resp = requests.post(
                    append_url,
                    auth=self.auth,
                    files={"media": chunk},
                    data={"segment_index": segment},
                )
                resp.raise_for_status()

        # FINALIZE
        finalize_url = f"https://api.x.com/2/media/upload/{media_id}/finalize"
        fin_resp = requests.post(finalize_url, auth=self.auth)
        fin_resp.raise_for_status()
        fin_data = fin_resp.json()

        # Poll for async processing (video/GIF)
        processing = fin_data.get("processing_info")
        while processing and processing.get("state") in ("pending", "in_progress"):
            wait = processing.get("check_after_secs", 5)
            time.sleep(wait)
            status_resp = requests.get(
                f"https://api.x.com/2/media/upload/{media_id}",
                auth=self.auth,
            )
            status_resp.raise_for_status()
            processing = status_resp.json().get("processing_info")

        return media_id
