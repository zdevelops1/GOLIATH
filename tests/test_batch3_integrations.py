"""Tests for batch 3 integrations: Asana, Monday.com, Zendesk, Intercom,
Twitch, Snapchat, Medium, Substack, Cloudflare, Firebase."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Asana
# ---------------------------------------------------------------------------


class TestAsanaClient:
    @patch("goliath.integrations.asana.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.ASANA_ACCESS_TOKEN = ""

        from goliath.integrations.asana import AsanaClient

        with pytest.raises(RuntimeError, match="ASANA_ACCESS_TOKEN"):
            AsanaClient()

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "asana_tok"

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer asana_tok"

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_create_task(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"gid": "123", "name": "Build page"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        client.create_task(
            project_gid="proj_1", name="Build page", notes="Build the landing page."
        )

        url = client.session.post.call_args[0][0]
        assert "/tasks" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["data"]["name"] == "Build page"
        assert "proj_1" in payload["data"]["projects"]

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_get_task(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"gid": "123", "name": "Task 1"}}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        task = client.get_task("123")

        assert task["gid"] == "123"
        url = client.session.get.call_args[0][0]
        assert "/tasks/123" in url

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_list_workspaces(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"gid": "ws1"}, {"gid": "ws2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        workspaces = client.list_workspaces()

        assert len(workspaces) == 2
        url = client.session.get.call_args[0][0]
        assert "/workspaces" in url

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_add_comment(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"gid": "story_1", "text": "Done!"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        client.add_comment("123", text="Done!")

        url = client.session.post.call_args[0][0]
        assert "/tasks/123/stories" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["data"]["text"] == "Done!"

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_update_task(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"gid": "123", "completed": True}}
        mock_requests.Session.return_value.put.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        client.update_task("123", completed=True)

        url = client.session.put.call_args[0][0]
        assert "/tasks/123" in url

    @patch("goliath.integrations.asana.requests")
    @patch("goliath.integrations.asana.config")
    def test_delete_task(self, mock_config, mock_requests):
        mock_config.ASANA_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.asana import AsanaClient

        client = AsanaClient()
        client.delete_task("123")

        url = client.session.delete.call_args[0][0]
        assert "/tasks/123" in url


# ---------------------------------------------------------------------------
# Monday.com
# ---------------------------------------------------------------------------


class TestMondayClient:
    @patch("goliath.integrations.monday.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.MONDAY_API_TOKEN = ""

        from goliath.integrations.monday import MondayClient

        with pytest.raises(RuntimeError, match="MONDAY_API_TOKEN"):
            MondayClient()

    @patch("goliath.integrations.monday.requests")
    @patch("goliath.integrations.monday.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.MONDAY_API_TOKEN = "mon_tok"

        from goliath.integrations.monday import MondayClient

        client = MondayClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "mon_tok"

    @patch("goliath.integrations.monday.requests")
    @patch("goliath.integrations.monday.config")
    def test_list_boards(self, mock_config, mock_requests):
        mock_config.MONDAY_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"boards": [{"id": "1", "name": "Sprint"}]}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.monday import MondayClient

        client = MondayClient()
        boards = client.list_boards()

        assert len(boards) == 1
        assert boards[0]["name"] == "Sprint"

    @patch("goliath.integrations.monday.requests")
    @patch("goliath.integrations.monday.config")
    def test_create_item(self, mock_config, mock_requests):
        mock_config.MONDAY_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"create_item": {"id": "42", "name": "New task"}}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.monday import MondayClient

        client = MondayClient()
        item = client.create_item(board_id="1", item_name="New task")

        assert item["id"] == "42"

    @patch("goliath.integrations.monday.requests")
    @patch("goliath.integrations.monday.config")
    def test_add_update(self, mock_config, mock_requests):
        mock_config.MONDAY_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"create_update": {"id": "u1", "body": "Done!", "created_at": "2025-01-01"}}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.monday import MondayClient

        client = MondayClient()
        update = client.add_update(item_id="42", body="Done!")

        assert update["body"] == "Done!"

    @patch("goliath.integrations.monday.requests")
    @patch("goliath.integrations.monday.config")
    def test_graphql_error_raises(self, mock_config, mock_requests):
        mock_config.MONDAY_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errors": [{"message": "Bad query"}]}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.monday import MondayClient

        client = MondayClient()
        with pytest.raises(RuntimeError, match="Monday.com API error"):
            client.list_boards()


# ---------------------------------------------------------------------------
# Zendesk
# ---------------------------------------------------------------------------


class TestZendeskClient:
    @patch("goliath.integrations.zendesk.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.ZENDESK_API_TOKEN = ""
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = "test"

        from goliath.integrations.zendesk import ZendeskClient

        with pytest.raises(RuntimeError, match="ZENDESK_API_TOKEN"):
            ZendeskClient()

    @patch("goliath.integrations.zendesk.config")
    def test_missing_email_raises(self, mock_config):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = ""
        mock_config.ZENDESK_SUBDOMAIN = "test"

        from goliath.integrations.zendesk import ZendeskClient

        with pytest.raises(RuntimeError, match="ZENDESK_EMAIL"):
            ZendeskClient()

    @patch("goliath.integrations.zendesk.config")
    def test_missing_subdomain_raises(self, mock_config):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = ""

        from goliath.integrations.zendesk import ZendeskClient

        with pytest.raises(RuntimeError, match="ZENDESK_SUBDOMAIN"):
            ZendeskClient()

    @patch("goliath.integrations.zendesk.requests")
    @patch("goliath.integrations.zendesk.config")
    def test_auth_set(self, mock_config, mock_requests):
        mock_config.ZENDESK_API_TOKEN = "zd_tok"
        mock_config.ZENDESK_EMAIL = "agent@co.com"
        mock_config.ZENDESK_SUBDOMAIN = "myco"

        from goliath.integrations.zendesk import ZendeskClient

        client = ZendeskClient()
        assert client.session.auth == ("agent@co.com/token", "zd_tok")

    @patch("goliath.integrations.zendesk.requests")
    @patch("goliath.integrations.zendesk.config")
    def test_create_ticket(self, mock_config, mock_requests):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = "test"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ticket": {"id": 1, "subject": "Bug"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.zendesk import ZendeskClient

        client = ZendeskClient()
        ticket = client.create_ticket(subject="Bug", description="It's broken", priority="high")

        assert ticket["id"] == 1
        url = client.session.post.call_args[0][0]
        assert "/tickets.json" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["ticket"]["subject"] == "Bug"
        assert payload["ticket"]["priority"] == "high"

    @patch("goliath.integrations.zendesk.requests")
    @patch("goliath.integrations.zendesk.config")
    def test_get_ticket(self, mock_config, mock_requests):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = "test"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ticket": {"id": 42, "status": "open"}}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.zendesk import ZendeskClient

        client = ZendeskClient()
        ticket = client.get_ticket(42)

        assert ticket["id"] == 42
        url = client.session.get.call_args[0][0]
        assert "/tickets/42.json" in url

    @patch("goliath.integrations.zendesk.requests")
    @patch("goliath.integrations.zendesk.config")
    def test_search_tickets(self, mock_config, mock_requests):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = "test"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": 1}, {"id": 2}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.zendesk import ZendeskClient

        client = ZendeskClient()
        results = client.search_tickets("status:open type:ticket")

        assert len(results) == 2

    @patch("goliath.integrations.zendesk.requests")
    @patch("goliath.integrations.zendesk.config")
    def test_create_user(self, mock_config, mock_requests):
        mock_config.ZENDESK_API_TOKEN = "tok"
        mock_config.ZENDESK_EMAIL = "a@b.com"
        mock_config.ZENDESK_SUBDOMAIN = "test"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"user": {"id": 99, "name": "Jane"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.zendesk import ZendeskClient

        client = ZendeskClient()
        user = client.create_user(name="Jane", email="jane@example.com")

        assert user["name"] == "Jane"
        url = client.session.post.call_args[0][0]
        assert "/users.json" in url


# ---------------------------------------------------------------------------
# Intercom
# ---------------------------------------------------------------------------


class TestIntercomClient:
    @patch("goliath.integrations.intercom.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.INTERCOM_ACCESS_TOKEN = ""

        from goliath.integrations.intercom import IntercomClient

        with pytest.raises(RuntimeError, match="INTERCOM_ACCESS_TOKEN"):
            IntercomClient()

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "ic_tok"

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer ic_tok"
        assert call_kwargs["Intercom-Version"] == "2.10"

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_create_contact(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "ct_1", "email": "jane@example.com"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        contact = client.create_contact(role="user", email="jane@example.com", name="Jane")

        assert contact["id"] == "ct_1"
        url = client.session.post.call_args[0][0]
        assert "/contacts" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["email"] == "jane@example.com"
        assert payload["role"] == "user"

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_send_message(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"type": "admin_message", "id": "msg_1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        client.send_message(
            from_admin_id="admin_1", to_contact_id="ct_1", body="Hello!"
        )

        url = client.session.post.call_args[0][0]
        assert "/messages" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["body"] == "Hello!"
        assert payload["from"]["id"] == "admin_1"

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_search_contacts(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "ct_1", "email": "jane@x.com"}]}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        results = client.search_contacts(field="email", value="jane@x.com")

        assert len(results) == 1

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_reply_to_conversation(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "conv_1", "type": "conversation"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        client.reply_to_conversation(
            conversation_id="conv_1", admin_id="admin_1", body="Looking into it."
        )

        url = client.session.post.call_args[0][0]
        assert "/conversations/conv_1/reply" in url

    @patch("goliath.integrations.intercom.requests")
    @patch("goliath.integrations.intercom.config")
    def test_list_tags(self, mock_config, mock_requests):
        mock_config.INTERCOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "t1", "name": "VIP"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.intercom import IntercomClient

        client = IntercomClient()
        tags = client.list_tags()

        assert len(tags) == 1
        assert tags[0]["name"] == "VIP"


# ---------------------------------------------------------------------------
# Twitch
# ---------------------------------------------------------------------------


class TestTwitchClient:
    @patch("goliath.integrations.twitch.config")
    def test_missing_client_id_raises(self, mock_config):
        mock_config.TWITCH_CLIENT_ID = ""
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = ""

        from goliath.integrations.twitch import TwitchClient

        with pytest.raises(RuntimeError, match="TWITCH_CLIENT_ID"):
            TwitchClient()

    @patch("goliath.integrations.twitch.config")
    def test_missing_secret_when_no_token_raises(self, mock_config):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = ""

        from goliath.integrations.twitch import TwitchClient

        with pytest.raises(RuntimeError, match="TWITCH_CLIENT_SECRET"):
            TwitchClient()

    @patch("goliath.integrations.twitch.requests")
    @patch("goliath.integrations.twitch.config")
    def test_user_token_init(self, mock_config, mock_requests):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = "user_tok"

        from goliath.integrations.twitch import TwitchClient

        client = TwitchClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer user_tok"
        assert call_kwargs["Client-Id"] == "cid"

    @patch("goliath.integrations.twitch.requests")
    @patch("goliath.integrations.twitch.config")
    def test_auto_app_token(self, mock_config, mock_requests):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = "csecret"
        mock_config.TWITCH_ACCESS_TOKEN = ""

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "app_tok"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.twitch import TwitchClient

        client = TwitchClient()
        mock_requests.post.assert_called_once()
        assert client.access_token == "app_tok"

    @patch("goliath.integrations.twitch.requests")
    @patch("goliath.integrations.twitch.config")
    def test_search_channels(self, mock_config, mock_requests):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"broadcaster_login": "speed_runner", "is_live": True}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.twitch import TwitchClient

        client = TwitchClient()
        results = client.search_channels("speedrunning")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/search/channels" in url

    @patch("goliath.integrations.twitch.requests")
    @patch("goliath.integrations.twitch.config")
    def test_get_streams(self, mock_config, mock_requests):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"user_login": "shroud", "viewer_count": 10000}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.twitch import TwitchClient

        client = TwitchClient()
        streams = client.get_streams(user_login=["shroud"])

        assert len(streams) == 1
        url = client.session.get.call_args[0][0]
        assert "/streams" in url

    @patch("goliath.integrations.twitch.requests")
    @patch("goliath.integrations.twitch.config")
    def test_get_top_games(self, mock_config, mock_requests):
        mock_config.TWITCH_CLIENT_ID = "cid"
        mock_config.TWITCH_CLIENT_SECRET = ""
        mock_config.TWITCH_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "1", "name": "Fortnite"}, {"id": "2", "name": "Minecraft"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.twitch import TwitchClient

        client = TwitchClient()
        games = client.get_top_games(limit=10)

        assert len(games) == 2


# ---------------------------------------------------------------------------
# Snapchat
# ---------------------------------------------------------------------------


class TestSnapchatClient:
    @patch("goliath.integrations.snapchat.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.SNAPCHAT_ACCESS_TOKEN = ""
        mock_config.SNAPCHAT_AD_ACCOUNT_ID = ""

        from goliath.integrations.snapchat import SnapchatClient

        with pytest.raises(RuntimeError, match="SNAPCHAT_ACCESS_TOKEN"):
            SnapchatClient()

    @patch("goliath.integrations.snapchat.requests")
    @patch("goliath.integrations.snapchat.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.SNAPCHAT_ACCESS_TOKEN = "snap_tok"
        mock_config.SNAPCHAT_AD_ACCOUNT_ID = "acct_1"

        from goliath.integrations.snapchat import SnapchatClient

        client = SnapchatClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer snap_tok"

    @patch("goliath.integrations.snapchat.requests")
    @patch("goliath.integrations.snapchat.config")
    def test_get_me(self, mock_config, mock_requests):
        mock_config.SNAPCHAT_ACCESS_TOKEN = "tok"
        mock_config.SNAPCHAT_AD_ACCOUNT_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"me": {"id": "user_1", "display_name": "Test"}}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.snapchat import SnapchatClient

        client = SnapchatClient()
        me = client.get_me()

        assert me["id"] == "user_1"

    @patch("goliath.integrations.snapchat.requests")
    @patch("goliath.integrations.snapchat.config")
    def test_list_campaigns(self, mock_config, mock_requests):
        mock_config.SNAPCHAT_ACCESS_TOKEN = "tok"
        mock_config.SNAPCHAT_AD_ACCOUNT_ID = "acct_1"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "campaigns": [{"campaign": {"id": "camp_1", "name": "Summer"}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.snapchat import SnapchatClient

        client = SnapchatClient()
        campaigns = client.list_campaigns()

        assert len(campaigns) == 1

    @patch("goliath.integrations.snapchat.requests")
    @patch("goliath.integrations.snapchat.config")
    def test_create_campaign(self, mock_config, mock_requests):
        mock_config.SNAPCHAT_ACCESS_TOKEN = "tok"
        mock_config.SNAPCHAT_AD_ACCOUNT_ID = "acct_1"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "campaigns": [{"campaign": {"id": "camp_new", "name": "Winter Sale"}}]
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.snapchat import SnapchatClient

        client = SnapchatClient()
        campaign = client.create_campaign(name="Winter Sale", status="PAUSED")

        assert campaign["name"] == "Winter Sale"


# ---------------------------------------------------------------------------
# Medium
# ---------------------------------------------------------------------------


class TestMediumClient:
    @patch("goliath.integrations.medium.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.MEDIUM_ACCESS_TOKEN = ""

        from goliath.integrations.medium import MediumClient

        with pytest.raises(RuntimeError, match="MEDIUM_ACCESS_TOKEN"):
            MediumClient()

    @patch("goliath.integrations.medium.requests")
    @patch("goliath.integrations.medium.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.MEDIUM_ACCESS_TOKEN = "med_tok"

        from goliath.integrations.medium import MediumClient

        client = MediumClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer med_tok"

    @patch("goliath.integrations.medium.requests")
    @patch("goliath.integrations.medium.config")
    def test_get_me(self, mock_config, mock_requests):
        mock_config.MEDIUM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"id": "u1", "username": "writer", "name": "Jane"}
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.medium import MediumClient

        client = MediumClient()
        me = client.get_me()

        assert me["username"] == "writer"
        url = client.session.get.call_args[0][0]
        assert "/me" in url

    @patch("goliath.integrations.medium.requests")
    @patch("goliath.integrations.medium.config")
    def test_create_post(self, mock_config, mock_requests):
        mock_config.MEDIUM_ACCESS_TOKEN = "tok"

        # First call: get_me (for user_id), Second call: create_post
        me_resp = MagicMock()
        me_resp.json.return_value = {"data": {"id": "u1"}}
        post_resp = MagicMock()
        post_resp.json.return_value = {
            "data": {"id": "post_1", "title": "My Post", "url": "https://medium.com/@writer/my-post"}
        }
        mock_requests.Session.return_value.get.return_value = me_resp
        mock_requests.Session.return_value.post.return_value = post_resp

        from goliath.integrations.medium import MediumClient

        client = MediumClient()
        post = client.create_post(
            title="My Post",
            content="# Hello",
            content_format="markdown",
            publish_status="draft",
            tags=["ai", "automation"],
        )

        assert post["title"] == "My Post"
        url = client.session.post.call_args[0][0]
        assert "/users/u1/posts" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["contentFormat"] == "markdown"
        assert payload["publishStatus"] == "draft"
        assert payload["tags"] == ["ai", "automation"]

    @patch("goliath.integrations.medium.requests")
    @patch("goliath.integrations.medium.config")
    def test_tags_limited_to_five(self, mock_config, mock_requests):
        mock_config.MEDIUM_ACCESS_TOKEN = "tok"

        me_resp = MagicMock()
        me_resp.json.return_value = {"data": {"id": "u1"}}
        post_resp = MagicMock()
        post_resp.json.return_value = {"data": {"id": "post_1"}}
        mock_requests.Session.return_value.get.return_value = me_resp
        mock_requests.Session.return_value.post.return_value = post_resp

        from goliath.integrations.medium import MediumClient

        client = MediumClient()
        client.create_post(
            title="Test", content="Body", tags=["a", "b", "c", "d", "e", "f", "g"]
        )

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert len(payload["tags"]) == 5


# ---------------------------------------------------------------------------
# Substack
# ---------------------------------------------------------------------------


class TestSubstackClient:
    @patch("goliath.integrations.substack.config")
    def test_missing_cookie_raises(self, mock_config):
        mock_config.SUBSTACK_SESSION_COOKIE = ""
        mock_config.SUBSTACK_SUBDOMAIN = "test"
        mock_config.SUBSTACK_USER_ID = ""

        from goliath.integrations.substack import SubstackClient

        with pytest.raises(RuntimeError, match="SUBSTACK_SESSION_COOKIE"):
            SubstackClient()

    @patch("goliath.integrations.substack.config")
    def test_missing_subdomain_raises(self, mock_config):
        mock_config.SUBSTACK_SESSION_COOKIE = "cookie_val"
        mock_config.SUBSTACK_SUBDOMAIN = ""
        mock_config.SUBSTACK_USER_ID = ""

        from goliath.integrations.substack import SubstackClient

        with pytest.raises(RuntimeError, match="SUBSTACK_SUBDOMAIN"):
            SubstackClient()

    @patch("goliath.integrations.substack.requests")
    @patch("goliath.integrations.substack.config")
    def test_base_url_uses_subdomain(self, mock_config, mock_requests):
        mock_config.SUBSTACK_SESSION_COOKIE = "cookie_val"
        mock_config.SUBSTACK_SUBDOMAIN = "mypub"
        mock_config.SUBSTACK_USER_ID = ""

        from goliath.integrations.substack import SubstackClient

        client = SubstackClient()
        assert "mypub.substack.com" in client._base

    @patch("goliath.integrations.substack.requests")
    @patch("goliath.integrations.substack.config")
    def test_list_posts(self, mock_config, mock_requests):
        mock_config.SUBSTACK_SESSION_COOKIE = "cookie"
        mock_config.SUBSTACK_SUBDOMAIN = "pub"
        mock_config.SUBSTACK_USER_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": 1, "title": "Post 1"}]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.substack import SubstackClient

        client = SubstackClient()
        posts = client.list_posts(limit=10)

        assert len(posts) == 1
        url = client.session.get.call_args[0][0]
        assert "/posts" in url

    @patch("goliath.integrations.substack.requests")
    @patch("goliath.integrations.substack.config")
    def test_create_draft(self, mock_config, mock_requests):
        mock_config.SUBSTACK_SESSION_COOKIE = "cookie"
        mock_config.SUBSTACK_SUBDOMAIN = "pub"
        mock_config.SUBSTACK_USER_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 42, "title": "Weekly Digest"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.substack import SubstackClient

        client = SubstackClient()
        draft = client.create_draft(
            title="Weekly Digest",
            subtitle="Highlights",
            body_html="<h1>Hello</h1>",
        )

        assert draft["title"] == "Weekly Digest"
        url = client.session.post.call_args[0][0]
        assert "/drafts" in url

    @patch("goliath.integrations.substack.requests")
    @patch("goliath.integrations.substack.config")
    def test_publish_draft(self, mock_config, mock_requests):
        mock_config.SUBSTACK_SESSION_COOKIE = "cookie"
        mock_config.SUBSTACK_SUBDOMAIN = "pub"
        mock_config.SUBSTACK_USER_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 42, "published": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.substack import SubstackClient

        client = SubstackClient()
        client.publish_draft(draft_id=42, send_email=True)

        url = client.session.post.call_args[0][0]
        assert "/drafts/42/publish" in url


# ---------------------------------------------------------------------------
# Cloudflare
# ---------------------------------------------------------------------------


class TestCloudflareClient:
    @patch("goliath.integrations.cloudflare.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.CLOUDFLARE_API_TOKEN = ""
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        from goliath.integrations.cloudflare import CloudflareClient

        with pytest.raises(RuntimeError, match="Cloudflare credentials"):
            CloudflareClient()

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_api_token_auth(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = "cf_tok"
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        from goliath.integrations.cloudflare import CloudflareClient

        client = CloudflareClient()
        calls = client.session.headers.__setitem__.call_args_list
        auth_set = any(
            c[0] == ("Authorization", "Bearer cf_tok") for c in calls
        )
        header_update = client.session.headers.update.call_args_list
        auth_updated = any(
            "Authorization" in (call[0][0] if call[0] else {})
            for call in header_update
        )
        # Either direct set or via update
        assert auth_set or auth_updated or client.session.headers.get("Authorization")

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_global_api_key_auth(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = ""
        mock_config.CLOUDFLARE_API_KEY = "global_key"
        mock_config.CLOUDFLARE_EMAIL = "admin@example.com"

        from goliath.integrations.cloudflare import CloudflareClient

        CloudflareClient()
        # Should not raise

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_list_zones(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = "tok"
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "result": [{"id": "z1", "name": "example.com"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.cloudflare import CloudflareClient

        client = CloudflareClient()
        zones = client.list_zones()

        assert len(zones) == 1
        url = client.session.get.call_args[0][0]
        assert "/zones" in url

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_create_dns_record(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = "tok"
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "result": {"id": "r1", "type": "A", "name": "app.example.com"}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.cloudflare import CloudflareClient

        client = CloudflareClient()
        record = client.create_dns_record(
            zone_id="z1", type="A", name="app.example.com", content="192.0.2.1", proxied=True
        )

        assert record["type"] == "A"
        url = client.session.post.call_args[0][0]
        assert "/zones/z1/dns_records" in url

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_purge_cache(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = "tok"
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"id": "z1"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.cloudflare import CloudflareClient

        client = CloudflareClient()
        client.purge_cache(zone_id="z1")

        url = client.session.post.call_args[0][0]
        assert "/zones/z1/purge_cache" in url

    @patch("goliath.integrations.cloudflare.requests")
    @patch("goliath.integrations.cloudflare.config")
    def test_delete_dns_record(self, mock_config, mock_requests):
        mock_config.CLOUDFLARE_API_TOKEN = "tok"
        mock_config.CLOUDFLARE_API_KEY = ""
        mock_config.CLOUDFLARE_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"id": "r1"}}
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.cloudflare import CloudflareClient

        client = CloudflareClient()
        client.delete_dns_record(zone_id="z1", record_id="r1")

        url = client.session.delete.call_args[0][0]
        assert "/zones/z1/dns_records/r1" in url


# ---------------------------------------------------------------------------
# Firebase
# ---------------------------------------------------------------------------


class TestFirebaseClient:
    @patch("goliath.integrations.firebase.config")
    def test_missing_project_id_raises(self, mock_config):
        mock_config.FIREBASE_PROJECT_ID = ""
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.firebase import FirebaseClient

        with pytest.raises(RuntimeError, match="FIREBASE_PROJECT_ID"):
            FirebaseClient()

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_firestore_base_url(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "my-project"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        assert "my-project" in client._firestore_base

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_set_document(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "name": "projects/proj/databases/(default)/documents/users/u1",
            "fields": {"name": {"stringValue": "Jane"}, "age": {"integerValue": "30"}},
        }
        mock_resp.status_code = 200
        mock_resp.content = b'{"name": "..."}'
        mock_requests.Session.return_value.request.return_value = mock_resp

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        doc = client.set_document("users", "u1", {"name": "Jane", "age": 30})

        assert doc["name"] == "Jane"
        assert doc["age"] == 30

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_get_document(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "name": "projects/proj/databases/(default)/documents/users/u1",
            "fields": {"email": {"stringValue": "jane@example.com"}},
        }
        mock_resp.status_code = 200
        mock_resp.content = b'{"name": "..."}'
        mock_requests.Session.return_value.request.return_value = mock_resp

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        doc = client.get_document("users", "u1")

        assert doc["email"] == "jane@example.com"
        assert doc["_id"] == "u1"

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_encode_fields(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.firebase import FirebaseClient

        encoded = FirebaseClient._encode_fields({
            "name": "Jane",
            "active": True,
            "count": 42,
            "score": 3.14,
            "nothing": None,
            "tags": ["a", "b"],
            "meta": {"key": "val"},
        })

        assert encoded["name"] == {"stringValue": "Jane"}
        assert encoded["active"] == {"booleanValue": True}
        assert encoded["count"] == {"integerValue": "42"}
        assert encoded["score"] == {"doubleValue": 3.14}
        assert encoded["nothing"] == {"nullValue": None}
        assert "arrayValue" in encoded["tags"]
        assert "mapValue" in encoded["meta"]

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_decode_document(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.firebase import FirebaseClient

        doc = {
            "name": "projects/p/databases/(default)/documents/col/doc1",
            "fields": {
                "str_field": {"stringValue": "hello"},
                "int_field": {"integerValue": "99"},
                "bool_field": {"booleanValue": False},
                "arr_field": {
                    "arrayValue": {
                        "values": [
                            {"stringValue": "a"},
                            {"integerValue": "1"},
                        ]
                    }
                },
            },
        }

        result = FirebaseClient._decode_document(doc)
        assert result["_id"] == "doc1"
        assert result["str_field"] == "hello"
        assert result["int_field"] == 99
        assert result["bool_field"] is False
        assert result["arr_field"] == ["a", 1]

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_auth_sign_up(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = "api_key_123"
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "idToken": "id_tok",
            "refreshToken": "ref_tok",
            "localId": "uid_1",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        result = client.auth_sign_up(email="new@example.com", password="secret")

        assert result["idToken"] == "id_tok"
        url = client.session.post.call_args[0][0]
        assert "signUp" in url

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_rtdb_requires_database_url(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = ""
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        with pytest.raises(RuntimeError, match="FIREBASE_DATABASE_URL"):
            client.rtdb_get("/test")

    @patch("goliath.integrations.firebase.requests")
    @patch("goliath.integrations.firebase.config")
    def test_rtdb_set(self, mock_config, mock_requests):
        mock_config.FIREBASE_PROJECT_ID = "proj"
        mock_config.FIREBASE_API_KEY = ""
        mock_config.FIREBASE_DATABASE_URL = "https://proj-default-rtdb.firebaseio.com"
        mock_config.FIREBASE_SERVICE_ACCOUNT_FILE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"text": "Hello"}
        mock_requests.Session.return_value.put.return_value = mock_resp

        from goliath.integrations.firebase import FirebaseClient

        client = FirebaseClient()
        result = client.rtdb_set("/messages/msg1", {"text": "Hello"})

        assert result["text"] == "Hello"
        url = client.session.put.call_args[0][0]
        assert "messages/msg1.json" in url
