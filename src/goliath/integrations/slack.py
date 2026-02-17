"""
Slack Integration — send messages, rich blocks, and files to Slack channels.

SETUP INSTRUCTIONS
==================

Option A — Incoming Webhook (simplest, no bot needed):

  1. Go to https://api.slack.com/apps and click "Create New App" > "From scratch".
  2. Select your workspace and give the app a name (e.g. "GOLIATH").
  3. Go to Features > Incoming Webhooks > Activate Incoming Webhooks.
  4. Click "Add New Webhook to Workspace" and select a channel.
  5. Copy the webhook URL and add it to your .env:
       SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx

  This only supports sending to the channel you selected. For multiple
  channels, use Option B.

Option B — Bot Token (full access, multiple channels):

  1. Go to https://api.slack.com/apps and create an app (or use the one above).
  2. Go to Features > OAuth & Permissions.
  3. Under "Bot Token Scopes", add:
       chat:write, chat:write.public, files:write
  4. Click "Install to Workspace" and copy the Bot User OAuth Token.
  5. Add it to your .env:
       SLACK_BOT_TOKEN=xoxb-your-bot-token

  With the bot token you can post to any public channel by name or ID.

Usage:
    from goliath.integrations.slack import SlackClient

    # --- Webhook mode (simple) ---
    sl = SlackClient()
    sl.send("Hello from GOLIATH!")

    # --- Bot token mode (multi-channel) ---
    sl = SlackClient()
    sl.send("Deploy complete.", channel="#deployments")

    # Rich message with blocks
    sl.send_blocks(
        channel="#alerts",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Alert:* CPU usage above 90%"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Server:*\\nprod-01"},
                    {"type": "mrkdwn", "text": "*Region:*\\nus-east-1"},
                ],
            },
        ],
        text="CPU Alert",  # fallback for notifications
    )

    # Upload a file
    sl.upload_file("report.csv", channel="#reports", message="Daily report attached.")
"""

from pathlib import Path

import requests

from goliath import config

_API_BASE = "https://slack.com/api"


class SlackClient:
    """Slack client supporting both webhook and bot token modes."""

    def __init__(self):
        self.webhook_url = config.SLACK_WEBHOOK_URL
        self.bot_token = config.SLACK_BOT_TOKEN

        if not self.webhook_url and not self.bot_token:
            raise RuntimeError(
                "Neither SLACK_WEBHOOK_URL nor SLACK_BOT_TOKEN is set. "
                "Add at least one to .env. "
                "See integrations/slack.py for setup instructions."
            )

    # -- public API --------------------------------------------------------

    def send(
        self,
        text: str,
        channel: str | None = None,
        username: str | None = None,
        icon_emoji: str | None = None,
    ) -> dict:
        """Send a plain text message.

        Args:
            text:       Message text (supports Slack mrkdwn formatting).
            channel:    Channel name or ID (bot token mode only).
            username:   Override the bot's display name.
            icon_emoji: Override the bot's icon (e.g. ":robot_face:").

        Returns:
            API response dict.
        """
        payload: dict = {"text": text}
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        if channel and self.bot_token:
            payload["channel"] = channel
            return self._api_post("chat.postMessage", json=payload)

        if self.webhook_url:
            return self._webhook_post(payload)

        if self.bot_token:
            raise ValueError(
                "Bot token mode requires a channel argument. "
                "Pass channel='#channel-name' or set SLACK_WEBHOOK_URL for a default channel."
            )

        raise RuntimeError("No Slack credentials configured.")

    def send_blocks(
        self,
        blocks: list[dict],
        text: str = "",
        channel: str | None = None,
    ) -> dict:
        """Send a rich message using Slack Block Kit.

        Args:
            blocks:  List of Block Kit block dicts.
                     See https://api.slack.com/block-kit
            text:    Fallback text for notifications.
            channel: Channel name or ID (bot token mode only).

        Returns:
            API response dict.
        """
        payload: dict = {"blocks": blocks}
        if text:
            payload["text"] = text

        if channel and self.bot_token:
            payload["channel"] = channel
            return self._api_post("chat.postMessage", json=payload)

        if self.webhook_url:
            return self._webhook_post(payload)

        raise ValueError("Bot token mode requires a channel argument.")

    def upload_file(
        self,
        file_path: str,
        channel: str,
        message: str = "",
    ) -> dict:
        """Upload a file to a Slack channel (requires bot token).

        Args:
            file_path: Path to the file to upload.
            channel:   Channel name or ID.
            message:   Optional message sent with the file.

        Returns:
            API response dict.
        """
        if not self.bot_token:
            raise RuntimeError(
                "File uploads require SLACK_BOT_TOKEN. "
                "Webhooks do not support file uploads."
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            resp = requests.post(
                f"{_API_BASE}/files.upload",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                data={
                    "channels": channel,
                    "initial_comment": message,
                    "filename": path.name,
                },
                files={"file": (path.name, f)},
            )

        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")
        return data

    # -- internal helpers --------------------------------------------------

    def _webhook_post(self, payload: dict) -> dict:
        """Post to the webhook URL."""
        resp = requests.post(self.webhook_url, json=payload)
        resp.raise_for_status()
        return {"status": "sent"}

    def _api_post(self, method: str, **kwargs) -> dict:
        """Post to a Slack Web API method using the bot token."""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.bot_token}"
        headers["Content-Type"] = "application/json; charset=utf-8"

        resp = requests.post(
            f"{_API_BASE}/{method}",
            headers=headers,
            **kwargs,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")
        return data
