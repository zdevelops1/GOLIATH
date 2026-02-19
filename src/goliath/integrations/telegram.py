"""
Telegram Integration — send messages, photos, and documents via Telegram Bot API.

SETUP INSTRUCTIONS
==================

1. Open Telegram and message @BotFather.

2. Send /newbot and follow the prompts to create a bot.
   BotFather will give you a token like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

3. Add the token to your .env file:
     TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

4. Get your chat ID (the channel/group/user to send messages to):
   - Add your bot to a group or start a DM with it.
   - Send a message to the bot.
   - Visit: https://api.telegram.org/bot{TOKEN}/getUpdates
   - Find "chat":{"id": ...} in the response — that's your chat ID.

5. Add the chat ID to your .env file:
     TELEGRAM_CHAT_ID=your-chat-id

   You can also pass chat_id directly to any method to send to
   different chats without changing the default.

Usage:
    from goliath.integrations.telegram import TelegramClient

    tg = TelegramClient()

    # Simple message
    tg.send("Hello from GOLIATH!")

    # Message with Markdown formatting
    tg.send("*Bold* and _italic_ text", parse_mode="Markdown")

    # Send a photo
    tg.send_photo("https://example.com/image.jpg", caption="Check this out")

    # Send a local file
    tg.send_document("/path/to/report.pdf", caption="Here's the report")
"""

from pathlib import Path

import requests

from goliath import config

_BASE_URL = "https://api.telegram.org/bot{token}"


class TelegramClient:
    """Telegram Bot API client for sending messages, photos, and documents."""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self.token = bot_token or config.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set. "
                "Add it to .env or pass bot_token to TelegramClient(). "
                "See integrations/telegram.py for setup instructions."
            )
        self.default_chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.api_url = _BASE_URL.format(token=self.token)

    # -- public API --------------------------------------------------------

    def send(
        self,
        text: str,
        chat_id: str | None = None,
        parse_mode: str | None = None,
        disable_preview: bool = False,
    ) -> dict:
        """Send a text message.

        Args:
            text:            Message text (up to 4096 characters).
            chat_id:         Target chat. Defaults to TELEGRAM_CHAT_ID.
            parse_mode:      "Markdown", "MarkdownV2", or "HTML". None for plain text.
            disable_preview: Disable link previews in the message.

        Returns:
            Telegram API response dict.
        """
        payload: dict = {
            "chat_id": self._resolve_chat(chat_id),
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if disable_preview:
            payload["disable_web_page_preview"] = True

        return self._post("sendMessage", json=payload)

    def send_photo(
        self,
        photo: str,
        caption: str = "",
        chat_id: str | None = None,
        parse_mode: str | None = None,
    ) -> dict:
        """Send a photo by URL or file path.

        Args:
            photo:      Public URL or local file path to an image.
            caption:    Optional caption (up to 1024 characters).
            chat_id:    Target chat. Defaults to TELEGRAM_CHAT_ID.
            parse_mode: Caption formatting mode.

        Returns:
            Telegram API response dict.
        """
        cid = self._resolve_chat(chat_id)
        path = Path(photo)

        if path.exists():
            data = {"chat_id": cid}
            if caption:
                data["caption"] = caption
            if parse_mode:
                data["parse_mode"] = parse_mode
            with open(path, "rb") as f:
                return self._post("sendPhoto", data=data, files={"photo": f})
        else:
            payload: dict = {"chat_id": cid, "photo": photo}
            if caption:
                payload["caption"] = caption
            if parse_mode:
                payload["parse_mode"] = parse_mode
            return self._post("sendPhoto", json=payload)

    def send_document(
        self,
        document: str,
        caption: str = "",
        chat_id: str | None = None,
    ) -> dict:
        """Send a document/file.

        Args:
            document: Local file path or public URL.
            caption:  Optional caption.
            chat_id:  Target chat. Defaults to TELEGRAM_CHAT_ID.

        Returns:
            Telegram API response dict.
        """
        cid = self._resolve_chat(chat_id)
        path = Path(document)

        if path.exists():
            data = {"chat_id": cid}
            if caption:
                data["caption"] = caption
            with open(path, "rb") as f:
                return self._post(
                    "sendDocument", data=data, files={"document": (path.name, f)}
                )
        else:
            payload: dict = {"chat_id": cid, "document": document}
            if caption:
                payload["caption"] = caption
            return self._post("sendDocument", json=payload)

    # -- internal helpers --------------------------------------------------

    def _resolve_chat(self, chat_id: str | None) -> str:
        cid = chat_id or self.default_chat_id
        if not cid:
            raise RuntimeError("No chat_id provided and TELEGRAM_CHAT_ID is not set.")
        return cid

    def _post(self, method: str, **kwargs) -> dict:
        resp = requests.post(f"{self.api_url}/{method}", **kwargs)
        resp.raise_for_status()
        return resp.json()
