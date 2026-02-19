"""Tests for social/messaging integrations: X, Instagram, Discord, Telegram, Slack, WhatsApp, Reddit."""

import unittest.mock
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ---------------------------------------------------------------------------
# X / Twitter
# ---------------------------------------------------------------------------

class TestXClient:

    @patch("goliath.integrations.x.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.X_CONSUMER_KEY = ""
        mock_config.X_CONSUMER_SECRET = "s"
        mock_config.X_ACCESS_TOKEN = "t"
        mock_config.X_ACCESS_TOKEN_SECRET = "ts"

        from goliath.integrations.x import XClient
        with pytest.raises(RuntimeError, match="Missing X/Twitter credentials"):
            XClient()

    @patch("goliath.integrations.x.requests")
    @patch("goliath.integrations.x.OAuth1")
    @patch("goliath.integrations.x.config")
    def test_tweet(self, mock_config, mock_oauth, mock_requests):
        mock_config.X_CONSUMER_KEY = "ck"
        mock_config.X_CONSUMER_SECRET = "cs"
        mock_config.X_ACCESS_TOKEN = "at"
        mock_config.X_ACCESS_TOKEN_SECRET = "ats"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"id": "123", "text": "Hello"}}
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.x import XClient
        client = XClient()
        result = client.tweet("Hello")

        mock_requests.post.assert_called_once()
        assert result["id"] == "123"

    @patch("goliath.integrations.x.requests")
    @patch("goliath.integrations.x.OAuth1")
    @patch("goliath.integrations.x.config")
    def test_thread(self, mock_config, mock_oauth, mock_requests):
        mock_config.X_CONSUMER_KEY = "ck"
        mock_config.X_CONSUMER_SECRET = "cs"
        mock_config.X_ACCESS_TOKEN = "at"
        mock_config.X_ACCESS_TOKEN_SECRET = "ats"

        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            resp = MagicMock()
            resp.json.return_value = {"data": {"id": str(call_count[0]), "text": "t"}}
            return resp

        mock_requests.post.side_effect = side_effect

        from goliath.integrations.x import XClient
        client = XClient()
        results = client.thread(["First", "Second"])

        assert len(results) == 2
        assert mock_requests.post.call_count == 2

    @patch("goliath.integrations.x.requests")
    @patch("goliath.integrations.x.OAuth1")
    @patch("goliath.integrations.x.config")
    def test_thread_empty_raises(self, mock_config, mock_oauth, mock_requests):
        mock_config.X_CONSUMER_KEY = "ck"
        mock_config.X_CONSUMER_SECRET = "cs"
        mock_config.X_ACCESS_TOKEN = "at"
        mock_config.X_ACCESS_TOKEN_SECRET = "ats"

        from goliath.integrations.x import XClient
        client = XClient()
        with pytest.raises(ValueError, match="at least one tweet"):
            client.thread([])


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

class TestInstagramClient:

    @patch("goliath.integrations.instagram.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.INSTAGRAM_ACCESS_TOKEN = ""
        mock_config.INSTAGRAM_USER_ID = "123"

        from goliath.integrations.instagram import InstagramClient
        with pytest.raises(RuntimeError, match="INSTAGRAM_ACCESS_TOKEN"):
            InstagramClient()

    @patch("goliath.integrations.instagram.config")
    def test_missing_user_id_raises(self, mock_config):
        mock_config.INSTAGRAM_ACCESS_TOKEN = "token"
        mock_config.INSTAGRAM_USER_ID = ""

        from goliath.integrations.instagram import InstagramClient
        with pytest.raises(RuntimeError, match="INSTAGRAM_USER_ID"):
            InstagramClient()

    @patch("goliath.integrations.instagram.requests")
    @patch("goliath.integrations.instagram.config")
    def test_post_image(self, mock_config, mock_requests):
        mock_config.INSTAGRAM_ACCESS_TOKEN = "token"
        mock_config.INSTAGRAM_USER_ID = "user1"

        container_resp = MagicMock()
        container_resp.json.return_value = {"id": "container_1"}
        publish_resp = MagicMock()
        publish_resp.json.return_value = {"id": "media_1"}
        mock_requests.post.side_effect = [container_resp, publish_resp]

        from goliath.integrations.instagram import InstagramClient
        client = InstagramClient()
        result = client.post_image("https://example.com/img.jpg", caption="Test")

        assert result["id"] == "media_1"
        assert mock_requests.post.call_count == 2
        # Verify token is in Authorization header, not body
        for call in mock_requests.post.call_args_list:
            headers = call.kwargs.get("headers", {})
            assert "Bearer" in headers.get("Authorization", "")

    @patch("goliath.integrations.instagram.requests")
    @patch("goliath.integrations.instagram.config")
    def test_carousel_min_items(self, mock_config, mock_requests):
        mock_config.INSTAGRAM_ACCESS_TOKEN = "token"
        mock_config.INSTAGRAM_USER_ID = "user1"

        from goliath.integrations.instagram import InstagramClient
        client = InstagramClient()
        with pytest.raises(ValueError, match="at least 2"):
            client.post_carousel([{"image_url": "https://example.com/1.jpg"}])


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

class TestDiscordClient:

    @patch("goliath.integrations.discord.config")
    def test_missing_webhook_raises(self, mock_config):
        mock_config.DISCORD_WEBHOOK_URL = ""

        from goliath.integrations.discord import DiscordClient
        with pytest.raises(RuntimeError, match="DISCORD_WEBHOOK_URL"):
            DiscordClient()

    @patch("goliath.integrations.discord.requests")
    @patch("goliath.integrations.discord.config")
    def test_send(self, mock_config, mock_requests):
        mock_config.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.discord import DiscordClient
        client = DiscordClient()
        result = client.send("Hello!")

        assert result["status"] == "sent"
        mock_requests.post.assert_called_once()

    @patch("goliath.integrations.discord.requests")
    @patch("goliath.integrations.discord.config")
    def test_send_embed(self, mock_config, mock_requests):
        mock_config.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.discord import DiscordClient
        client = DiscordClient()
        result = client.send_embed(title="Test", description="Body", color=0xFF0000)

        assert result["status"] == "sent"
        call_kwargs = mock_requests.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["embeds"][0]["title"] == "Test"
        assert payload["embeds"][0]["color"] == 0xFF0000

    @patch("goliath.integrations.discord.config")
    def test_send_file_not_found(self, mock_config):
        mock_config.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"

        from goliath.integrations.discord import DiscordClient
        client = DiscordClient()
        with pytest.raises(FileNotFoundError):
            client.send_file("/nonexistent/file.txt")


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

class TestTelegramClient:

    @patch("goliath.integrations.telegram.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.TELEGRAM_BOT_TOKEN = ""
        mock_config.TELEGRAM_CHAT_ID = ""

        from goliath.integrations.telegram import TelegramClient
        with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
            TelegramClient()

    @patch("goliath.integrations.telegram.requests")
    @patch("goliath.integrations.telegram.config")
    def test_send(self, mock_config, mock_requests):
        mock_config.TELEGRAM_BOT_TOKEN = "123:ABC"
        mock_config.TELEGRAM_CHAT_ID = "chat_1"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.telegram import TelegramClient
        client = TelegramClient()
        result = client.send("Hello!")

        mock_requests.post.assert_called_once()
        url = mock_requests.post.call_args[0][0]
        assert "sendMessage" in url
        assert "123:ABC" in url

    @patch("goliath.integrations.telegram.config")
    def test_no_chat_id_raises(self, mock_config):
        mock_config.TELEGRAM_BOT_TOKEN = "123:ABC"
        mock_config.TELEGRAM_CHAT_ID = ""

        from goliath.integrations.telegram import TelegramClient
        client = TelegramClient()
        with pytest.raises(RuntimeError, match="No chat_id"):
            client.send("Hello!")


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

class TestSlackClient:

    @patch("goliath.integrations.slack.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.SLACK_WEBHOOK_URL = ""
        mock_config.SLACK_BOT_TOKEN = ""

        from goliath.integrations.slack import SlackClient
        with pytest.raises(RuntimeError, match="SLACK_WEBHOOK_URL.*SLACK_BOT_TOKEN"):
            SlackClient()

    @patch("goliath.integrations.slack.requests")
    @patch("goliath.integrations.slack.config")
    def test_send_via_webhook(self, mock_config, mock_requests):
        mock_config.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/T/B/xxx"
        mock_config.SLACK_BOT_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.slack import SlackClient
        client = SlackClient()
        result = client.send("Hello!")

        assert result["status"] == "sent"

    @patch("goliath.integrations.slack.requests")
    @patch("goliath.integrations.slack.config")
    def test_send_via_bot_token(self, mock_config, mock_requests):
        mock_config.SLACK_WEBHOOK_URL = ""
        mock_config.SLACK_BOT_TOKEN = "xoxb-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True, "channel": "C123"}
        mock_requests.post.return_value = mock_resp

        from goliath.integrations.slack import SlackClient
        client = SlackClient()
        result = client.send("Hello!", channel="#general")

        assert result["ok"] is True
        call_kwargs = mock_requests.post.call_args
        assert "Bearer xoxb-token" in call_kwargs.kwargs.get("headers", {}).get("Authorization", "")

    @patch("goliath.integrations.slack.config")
    def test_bot_token_requires_channel(self, mock_config):
        mock_config.SLACK_WEBHOOK_URL = ""
        mock_config.SLACK_BOT_TOKEN = "xoxb-token"

        from goliath.integrations.slack import SlackClient
        client = SlackClient()
        with pytest.raises(ValueError, match="channel"):
            client.send("Hello!")

    @patch("goliath.integrations.slack.config")
    def test_upload_file_requires_bot_token(self, mock_config):
        mock_config.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/T/B/xxx"
        mock_config.SLACK_BOT_TOKEN = ""

        from goliath.integrations.slack import SlackClient
        client = SlackClient()
        with pytest.raises(RuntimeError, match="SLACK_BOT_TOKEN"):
            client.upload_file("file.txt", "#channel")


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------

class TestWhatsAppClient:

    @patch("goliath.integrations.whatsapp.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = ""
        mock_config.WHATSAPP_PHONE_ID = "123"

        from goliath.integrations.whatsapp import WhatsAppClient
        with pytest.raises(RuntimeError, match="WHATSAPP_ACCESS_TOKEN"):
            WhatsAppClient()

    @patch("goliath.integrations.whatsapp.config")
    def test_missing_phone_id_raises(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = "token"
        mock_config.WHATSAPP_PHONE_ID = ""

        from goliath.integrations.whatsapp import WhatsAppClient
        with pytest.raises(RuntimeError, match="WHATSAPP_PHONE_ID"):
            WhatsAppClient()

    @patch("goliath.integrations.whatsapp.config")
    def test_send_text(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = "token"
        mock_config.WHATSAPP_PHONE_ID = "phone_1"

        from goliath.integrations.whatsapp import WhatsAppClient
        client = WhatsAppClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "msg_1"}]}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.send_text(to="15551234567", body="Hello!")

        call_kwargs = client.session.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["to"] == "15551234567"
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Hello!"
        assert "Bearer" in client.session.headers["Authorization"]

    @patch("goliath.integrations.whatsapp.config")
    def test_send_image_requires_url_or_id(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = "token"
        mock_config.WHATSAPP_PHONE_ID = "phone_1"

        from goliath.integrations.whatsapp import WhatsAppClient
        client = WhatsAppClient()
        with pytest.raises(ValueError, match="image_url or image_id"):
            client.send_image(to="15551234567")

    @patch("goliath.integrations.whatsapp.config")
    def test_send_template(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = "token"
        mock_config.WHATSAPP_PHONE_ID = "phone_1"

        from goliath.integrations.whatsapp import WhatsAppClient
        client = WhatsAppClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "msg_1"}]}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.send_template(to="15551234567", template_name="hello_world")

        payload = client.session.post.call_args.kwargs["json"]
        assert payload["type"] == "template"
        assert payload["template"]["name"] == "hello_world"

    @patch("goliath.integrations.whatsapp.config")
    def test_send_location(self, mock_config):
        mock_config.WHATSAPP_ACCESS_TOKEN = "token"
        mock_config.WHATSAPP_PHONE_ID = "phone_1"

        from goliath.integrations.whatsapp import WhatsAppClient
        client = WhatsAppClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "msg_1"}]}
        client.session.post = MagicMock(return_value=mock_resp)

        client.send_location(to="15551234567", latitude=37.77, longitude=-122.42, name="SF")
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["type"] == "location"
        assert payload["location"]["name"] == "SF"


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------

class TestRedditClient:

    @patch("goliath.integrations.reddit.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.REDDIT_CLIENT_ID = ""
        mock_config.REDDIT_CLIENT_SECRET = ""
        mock_config.REDDIT_USERNAME = ""
        mock_config.REDDIT_PASSWORD = ""

        from goliath.integrations.reddit import RedditClient
        with pytest.raises(RuntimeError, match="Missing Reddit credentials"):
            RedditClient()

    @patch("goliath.integrations.reddit.requests")
    @patch("goliath.integrations.reddit.config")
    def test_authenticate_and_submit_text(self, mock_config, mock_requests):
        mock_config.REDDIT_CLIENT_ID = "cid"
        mock_config.REDDIT_CLIENT_SECRET = "csecret"
        mock_config.REDDIT_USERNAME = "user"
        mock_config.REDDIT_PASSWORD = "pass"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "tok123", "token_type": "bearer"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.reddit import RedditClient
        client = RedditClient()

        # Verify auth was called
        mock_requests.post.assert_called_once()
        auth_call = mock_requests.post.call_args
        assert "access_token" in str(auth_call)

        # Now test submit_text
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"json": {"data": {"url": "https://reddit.com/r/test/1"}}}
        submit_resp.status_code = 200
        submit_resp.content = b'{"json": {}}'
        client.session.post = MagicMock(return_value=submit_resp)

        result = client.submit_text("test", title="Hello", text="Body")
        call_kwargs = client.session.post.call_args.kwargs
        assert call_kwargs["data"]["sr"] == "test"
        assert call_kwargs["data"]["kind"] == "self"

    @patch("goliath.integrations.reddit.requests")
    @patch("goliath.integrations.reddit.config")
    def test_oauth_failure_sanitized(self, mock_config, mock_requests):
        mock_config.REDDIT_CLIENT_ID = "cid"
        mock_config.REDDIT_CLIENT_SECRET = "csecret"
        mock_config.REDDIT_USERNAME = "user"
        mock_config.REDDIT_PASSWORD = "pass"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"error": "invalid_grant", "error_description": "bad creds"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.reddit import RedditClient
        with pytest.raises(RuntimeError, match="invalid_grant"):
            RedditClient()

    @patch("goliath.integrations.reddit.requests")
    @patch("goliath.integrations.reddit.config")
    def test_vote_validates_direction(self, mock_config, mock_requests):
        mock_config.REDDIT_CLIENT_ID = "cid"
        mock_config.REDDIT_CLIENT_SECRET = "csecret"
        mock_config.REDDIT_USERNAME = "user"
        mock_config.REDDIT_PASSWORD = "pass"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "tok123"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.reddit import RedditClient
        client = RedditClient()
        with pytest.raises(ValueError, match="direction must be"):
            client.vote("t3_abc", direction=2)

    @patch("goliath.integrations.reddit.requests")
    @patch("goliath.integrations.reddit.config")
    def test_user_agent_includes_username(self, mock_config, mock_requests):
        mock_config.REDDIT_CLIENT_ID = "cid"
        mock_config.REDDIT_CLIENT_SECRET = "csecret"
        mock_config.REDDIT_USERNAME = "testuser"
        mock_config.REDDIT_PASSWORD = "pass"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "tok123"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.reddit import RedditClient
        client = RedditClient()
        # session.headers is a mock; check the __setitem__ call
        client.session.headers.__setitem__.assert_any_call(
            "User-Agent", unittest.mock.ANY,
        )
        ua_value = client.session.headers.__setitem__.call_args_list
        ua_set = [c for c in ua_value if c[0][0] == "User-Agent"]
        assert ua_set, "User-Agent was never set"
        assert "testuser" in ua_set[-1][0][1]
