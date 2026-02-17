"""
Discord Integration — send messages to Discord channels via webhooks.

SETUP INSTRUCTIONS
==================

1. Open Discord and go to the channel you want GOLIATH to post in.

2. Click the gear icon (Edit Channel) > Integrations > Webhooks.

3. Click "New Webhook", give it a name (e.g. "GOLIATH"), and copy the
   webhook URL. It looks like:
   https://discord.com/api/webhooks/123456789/abcdefg...

4. Add the URL to your .env file:
     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefg...

   You can also set multiple webhooks for different channels by passing
   the URL directly to the client:
     client = DiscordClient(webhook_url="https://discord.com/api/webhooks/...")

That's it. No bot token, no OAuth, no server permissions needed.

Usage:
    from goliath.integrations.discord import DiscordClient

    dc = DiscordClient()

    # Simple message
    dc.send("Hello from GOLIATH!")

    # Message with a custom username and avatar
    dc.send("Deploying now.", username="GOLIATH Deploy", avatar_url="https://example.com/icon.png")

    # Rich embed
    dc.send_embed(
        title="Task Complete",
        description="GOLIATH finished processing your request.",
        color=0x00FF00,
        fields=[
            {"name": "Provider", "value": "Grok", "inline": True},
            {"name": "Tokens", "value": "312", "inline": True},
        ],
    )

    # Upload a file
    dc.send_file("report.txt", message="Here's the report.")
"""

from pathlib import Path

import requests

from goliath import config


class DiscordClient:
    """Discord webhook client for sending messages, embeds, and files."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or config.DISCORD_WEBHOOK_URL
        if not self.webhook_url:
            raise RuntimeError(
                "DISCORD_WEBHOOK_URL is not set. "
                "Add it to .env or pass webhook_url to DiscordClient(). "
                "See integrations/discord.py for setup instructions."
            )

    # -- public API --------------------------------------------------------

    def send(
        self,
        content: str,
        username: str | None = None,
        avatar_url: str | None = None,
    ) -> dict:
        """Send a plain text message to the Discord channel.

        Args:
            content:    Message text (up to 2000 characters).
            username:   Override the webhook's default display name.
            avatar_url: Override the webhook's default avatar.

        Returns:
            Discord API response dict.
        """
        payload: dict = {"content": content}
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url

        return self._post(json=payload)

    def send_embed(
        self,
        title: str = "",
        description: str = "",
        color: int = 0x5865F2,
        fields: list[dict] | None = None,
        footer: str | None = None,
        image_url: str | None = None,
        thumbnail_url: str | None = None,
        username: str | None = None,
    ) -> dict:
        """Send a rich embed message.

        Args:
            title:         Embed title.
            description:   Embed body text.
            color:         Sidebar color as hex int (default: Discord blurple).
            fields:        List of {"name": str, "value": str, "inline": bool}.
            footer:        Small text at the bottom of the embed.
            image_url:     Full-size image URL shown in the embed.
            thumbnail_url: Small thumbnail URL shown top-right.
            username:      Override the webhook's display name.

        Returns:
            Discord API response dict.
        """
        embed: dict = {"color": color}
        if title:
            embed["title"] = title
        if description:
            embed["description"] = description
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = {"text": footer}
        if image_url:
            embed["image"] = {"url": image_url}
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        payload: dict = {"embeds": [embed]}
        if username:
            payload["username"] = username

        return self._post(json=payload)

    def send_file(
        self,
        file_path: str,
        message: str = "",
        username: str | None = None,
    ) -> dict:
        """Upload a file to the Discord channel.

        Args:
            file_path: Path to the file to upload (max 25 MB on most servers).
            message:   Optional message text sent alongside the file.
            username:  Override the webhook's display name.

        Returns:
            Discord API response dict.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        payload = {}
        if message:
            payload["content"] = message
        if username:
            payload["username"] = username

        with open(path, "rb") as f:
            return self._post(
                data=payload,
                files={"file": (path.name, f)},
            )

    # -- internal helpers --------------------------------------------------

    def _post(self, **kwargs) -> dict:
        """Send a POST request to the webhook URL."""
        resp = requests.post(self.webhook_url, **kwargs)
        resp.raise_for_status()
        # Discord returns 204 No Content on success for most webhook calls
        if resp.status_code == 204 or not resp.content:
            return {"status": "sent"}
        return resp.json()
