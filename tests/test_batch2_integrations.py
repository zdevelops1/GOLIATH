"""Tests for batch 2 integrations: Pinterest, TikTok, Spotify, Zoom, Calendly,
HubSpot, Salesforce, WordPress, Webflow, PayPal."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Pinterest
# ---------------------------------------------------------------------------


class TestPinterestClient:
    @patch("goliath.integrations.pinterest.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.PINTEREST_ACCESS_TOKEN = ""

        from goliath.integrations.pinterest import PinterestClient

        with pytest.raises(RuntimeError, match="PINTEREST_ACCESS_TOKEN"):
            PinterestClient()

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "pin_tok"

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer pin_tok"

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_create_pin(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "pin_1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        client.create_pin(
            board_id="board_1",
            title="My Pin",
            image_url="https://example.com/img.jpg",
        )

        call_args = client.session.post.call_args
        url = call_args[0][0]
        assert "/pins" in url
        payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
        assert payload["board_id"] == "board_1"
        assert payload["title"] == "My Pin"
        assert payload["media_source"]["url"] == "https://example.com/img.jpg"

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_list_boards(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"id": "b1"}, {"id": "b2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        boards = client.list_boards(page_size=10)

        assert len(boards) == 2
        url = client.session.get.call_args[0][0]
        assert "/boards" in url

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_create_board(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "new_board"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        client.create_board(name="Recipes", privacy="SECRET")

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["name"] == "Recipes"
        assert payload["privacy"] == "SECRET"

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_search_pins(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"id": "p1"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        results = client.search_pins("home decor", page_size=5)

        assert len(results) == 1
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["query"] == "home decor"

    @patch("goliath.integrations.pinterest.requests")
    @patch("goliath.integrations.pinterest.config")
    def test_delete_pin(self, mock_config, mock_requests):
        mock_config.PINTEREST_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.pinterest import PinterestClient

        client = PinterestClient()
        client.delete_pin("pin_1")

        url = client.session.delete.call_args[0][0]
        assert "/pins/pin_1" in url


# ---------------------------------------------------------------------------
# TikTok
# ---------------------------------------------------------------------------


class TestTikTokClient:
    @patch("goliath.integrations.tiktok.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.TIKTOK_ACCESS_TOKEN = ""

        from goliath.integrations.tiktok import TikTokClient

        with pytest.raises(RuntimeError, match="TIKTOK_ACCESS_TOKEN"):
            TikTokClient()

    @patch("goliath.integrations.tiktok.requests")
    @patch("goliath.integrations.tiktok.config")
    def test_get_user_info(self, mock_config, mock_requests):
        mock_config.TIKTOK_ACCESS_TOKEN = "tt_tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"user": {"display_name": "TestUser"}}}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.tiktok import TikTokClient

        client = TikTokClient()
        user = client.get_user_info()

        assert user["display_name"] == "TestUser"
        url = client.session.get.call_args[0][0]
        assert "/user/info/" in url

    @patch("goliath.integrations.tiktok.requests")
    @patch("goliath.integrations.tiktok.config")
    def test_list_videos(self, mock_config, mock_requests):
        mock_config.TIKTOK_ACCESS_TOKEN = "tt_tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"videos": [{"id": "v1"}], "cursor": 100}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.tiktok import TikTokClient

        client = TikTokClient()
        data = client.list_videos(max_count=10)

        assert "videos" in data
        url = client.session.post.call_args[0][0]
        assert "/video/list/" in url

    @patch("goliath.integrations.tiktok.requests")
    @patch("goliath.integrations.tiktok.config")
    def test_publish_video_from_url(self, mock_config, mock_requests):
        mock_config.TIKTOK_ACCESS_TOKEN = "tt_tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"publish_id": "pub_1"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.tiktok import TikTokClient

        client = TikTokClient()
        result = client.publish_video_from_url(
            video_url="https://example.com/vid.mp4",
            title="Test Video",
            privacy_level="PUBLIC_TO_EVERYONE",
        )

        assert result["publish_id"] == "pub_1"
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["source_info"]["video_url"] == "https://example.com/vid.mp4"
        assert payload["post_info"]["title"] == "Test Video"
        assert payload["post_info"]["privacy_level"] == "PUBLIC_TO_EVERYONE"

    @patch("goliath.integrations.tiktok.requests")
    @patch("goliath.integrations.tiktok.config")
    def test_query_videos(self, mock_config, mock_requests):
        mock_config.TIKTOK_ACCESS_TOKEN = "tt_tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"videos": [{"id": "v1"}, {"id": "v2"}]}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.tiktok import TikTokClient

        client = TikTokClient()
        videos = client.query_videos(["v1", "v2"])

        assert len(videos) == 2
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["filters"]["video_ids"] == ["v1", "v2"]

    @patch("goliath.integrations.tiktok.requests")
    @patch("goliath.integrations.tiktok.config")
    def test_get_comments(self, mock_config, mock_requests):
        mock_config.TIKTOK_ACCESS_TOKEN = "tt_tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"comments": [{"id": "c1", "text": "Nice!"}]}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.tiktok import TikTokClient

        client = TikTokClient()
        data = client.get_comments("vid_1", max_count=10)

        assert "comments" in data
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["video_id"] == "vid_1"


# ---------------------------------------------------------------------------
# Spotify
# ---------------------------------------------------------------------------


class TestSpotifyClient:
    @patch("goliath.integrations.spotify.config")
    def test_no_credentials_raises(self, mock_config):
        mock_config.SPOTIFY_ACCESS_TOKEN = ""
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        from goliath.integrations.spotify import SpotifyClient

        with pytest.raises(RuntimeError, match="Spotify credentials"):
            SpotifyClient()

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_user_token_init(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "user_tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        client.session.headers.__setitem__.assert_any_call(
            "Authorization", "Bearer user_tok"
        )

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_client_credentials_flow(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = ""
        mock_config.SPOTIFY_CLIENT_ID = "client_id"
        mock_config.SPOTIFY_CLIENT_SECRET = "client_secret"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "cc_token"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.spotify import SpotifyClient

        SpotifyClient()
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "token" in call_args[0][0]
        assert call_args.kwargs.get("auth") == (
            "client_id",
            "client_secret",
        ) or call_args[1].get("auth") == ("client_id", "client_secret")

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "tracks": {"items": [{"name": "Bohemian Rhapsody"}]}
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        results = client.search("Bohemian Rhapsody", search_type="track", limit=5)

        assert "tracks" in results
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["q"] == "Bohemian Rhapsody"
        assert params["type"] == "track"
        assert params["limit"] == 5

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_create_playlist(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "pl_1"}
        mock_resp.status_code = 201
        mock_resp.content = b'{"id": "pl_1"}'
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        client.create_playlist(user_id="user1", name="My Playlist")

        url = client.session.post.call_args[0][0]
        assert "/users/user1/playlists" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["name"] == "My Playlist"

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_add_to_playlist(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"snapshot_id": "snap_1"}
        mock_resp.status_code = 201
        mock_resp.content = b'{"snapshot_id": "snap_1"}'
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        client.add_to_playlist("pl_1", uris=["spotify:track:abc"])

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["uris"] == ["spotify:track:abc"]

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_get_currently_playing_none(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        result = client.get_currently_playing()

        assert result is None

    @patch("goliath.integrations.spotify.requests")
    @patch("goliath.integrations.spotify.config")
    def test_get_artist_top_tracks(self, mock_config, mock_requests):
        mock_config.SPOTIFY_ACCESS_TOKEN = "tok"
        mock_config.SPOTIFY_CLIENT_ID = ""
        mock_config.SPOTIFY_CLIENT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"tracks": [{"name": "Track 1"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.spotify import SpotifyClient

        client = SpotifyClient()
        tracks = client.get_artist_top_tracks("artist_1", market="GB")

        assert len(tracks) == 1
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["market"] == "GB"


# ---------------------------------------------------------------------------
# Zoom
# ---------------------------------------------------------------------------


class TestZoomClient:
    @patch("goliath.integrations.zoom.config")
    def test_no_credentials_raises(self, mock_config):
        mock_config.ZOOM_ACCOUNT_ID = ""
        mock_config.ZOOM_CLIENT_ID = ""
        mock_config.ZOOM_CLIENT_SECRET = ""
        mock_config.ZOOM_ACCESS_TOKEN = ""

        from goliath.integrations.zoom import ZoomClient

        with pytest.raises(RuntimeError, match="Zoom credentials"):
            ZoomClient()

    @patch("goliath.integrations.zoom.requests")
    @patch("goliath.integrations.zoom.config")
    def test_user_token_init(self, mock_config, mock_requests):
        mock_config.ZOOM_ACCOUNT_ID = ""
        mock_config.ZOOM_CLIENT_ID = ""
        mock_config.ZOOM_CLIENT_SECRET = ""
        mock_config.ZOOM_ACCESS_TOKEN = "zoom_tok"

        from goliath.integrations.zoom import ZoomClient

        client = ZoomClient()
        client.session.headers.__setitem__.assert_any_call(
            "Authorization", "Bearer zoom_tok"
        )

    @patch("goliath.integrations.zoom.requests")
    @patch("goliath.integrations.zoom.config")
    def test_s2s_auth(self, mock_config, mock_requests):
        mock_config.ZOOM_ACCOUNT_ID = "acct_1"
        mock_config.ZOOM_CLIENT_ID = "cid"
        mock_config.ZOOM_CLIENT_SECRET = "csecret"
        mock_config.ZOOM_ACCESS_TOKEN = ""

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "s2s_token"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.zoom import ZoomClient

        ZoomClient()
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "oauth/token" in call_args[0][0]

    @patch("goliath.integrations.zoom.requests")
    @patch("goliath.integrations.zoom.config")
    def test_create_meeting(self, mock_config, mock_requests):
        mock_config.ZOOM_ACCOUNT_ID = ""
        mock_config.ZOOM_CLIENT_ID = ""
        mock_config.ZOOM_CLIENT_SECRET = ""
        mock_config.ZOOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": 123,
            "join_url": "https://zoom.us/j/123",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.zoom import ZoomClient

        client = ZoomClient()
        client.create_meeting(
            topic="Standup", start_time="2025-06-01T09:00:00Z", duration=30
        )

        url = client.session.post.call_args[0][0]
        assert "/users/me/meetings" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["topic"] == "Standup"
        assert payload["duration"] == 30

    @patch("goliath.integrations.zoom.requests")
    @patch("goliath.integrations.zoom.config")
    def test_list_meetings(self, mock_config, mock_requests):
        mock_config.ZOOM_ACCOUNT_ID = ""
        mock_config.ZOOM_CLIENT_ID = ""
        mock_config.ZOOM_CLIENT_SECRET = ""
        mock_config.ZOOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"meetings": [{"id": 1, "topic": "Meeting 1"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.zoom import ZoomClient

        client = ZoomClient()
        meetings = client.list_meetings()

        assert len(meetings) == 1
        url = client.session.get.call_args[0][0]
        assert "/users/me/meetings" in url

    @patch("goliath.integrations.zoom.requests")
    @patch("goliath.integrations.zoom.config")
    def test_delete_meeting(self, mock_config, mock_requests):
        mock_config.ZOOM_ACCOUNT_ID = ""
        mock_config.ZOOM_CLIENT_ID = ""
        mock_config.ZOOM_CLIENT_SECRET = ""
        mock_config.ZOOM_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.zoom import ZoomClient

        client = ZoomClient()
        client.delete_meeting(123456)

        url = client.session.delete.call_args[0][0]
        assert "/meetings/123456" in url


# ---------------------------------------------------------------------------
# Calendly
# ---------------------------------------------------------------------------


class TestCalendlyClient:
    @patch("goliath.integrations.calendly.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.CALENDLY_ACCESS_TOKEN = ""

        from goliath.integrations.calendly import CalendlyClient

        with pytest.raises(RuntimeError, match="CALENDLY_ACCESS_TOKEN"):
            CalendlyClient()

    @patch("goliath.integrations.calendly.requests")
    @patch("goliath.integrations.calendly.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.CALENDLY_ACCESS_TOKEN = "cal_tok"

        from goliath.integrations.calendly import CalendlyClient

        client = CalendlyClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer cal_tok"

    @patch("goliath.integrations.calendly.requests")
    @patch("goliath.integrations.calendly.config")
    def test_get_current_user(self, mock_config, mock_requests):
        mock_config.CALENDLY_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "resource": {
                "uri": "https://api.calendly.com/users/abc",
                "name": "Jane",
            }
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.calendly import CalendlyClient

        client = CalendlyClient()
        user = client.get_current_user()

        assert user["name"] == "Jane"
        assert client._user_uri == "https://api.calendly.com/users/abc"

    @patch("goliath.integrations.calendly.requests")
    @patch("goliath.integrations.calendly.config")
    def test_list_event_types_resolves_user(self, mock_config, mock_requests):
        mock_config.CALENDLY_ACCESS_TOKEN = "tok"

        # First call: get_current_user (to resolve user_uri)
        # Second call: list_event_types
        user_resp = MagicMock()
        user_resp.json.return_value = {
            "resource": {"uri": "https://api.calendly.com/users/abc"}
        }
        types_resp = MagicMock()
        types_resp.json.return_value = {
            "collection": [{"uri": "evt_type_1"}, {"uri": "evt_type_2"}]
        }
        mock_requests.Session.return_value.get.side_effect = [user_resp, types_resp]

        from goliath.integrations.calendly import CalendlyClient

        client = CalendlyClient()
        event_types = client.list_event_types()

        assert len(event_types) == 2

    @patch("goliath.integrations.calendly.requests")
    @patch("goliath.integrations.calendly.config")
    def test_cancel_event(self, mock_config, mock_requests):
        mock_config.CALENDLY_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"resource": {"status": "canceled"}}
        mock_resp.status_code = 200
        mock_resp.content = b'{"resource": {}}'
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.calendly import CalendlyClient

        client = CalendlyClient()
        client.cancel_event("evt_uuid", reason="Changed plans")

        url = client.session.post.call_args[0][0]
        assert "/scheduled_events/evt_uuid/cancellation" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["reason"] == "Changed plans"

    @patch("goliath.integrations.calendly.requests")
    @patch("goliath.integrations.calendly.config")
    def test_list_event_invitees(self, mock_config, mock_requests):
        mock_config.CALENDLY_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"collection": [{"email": "guest@example.com"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.calendly import CalendlyClient

        client = CalendlyClient()
        invitees = client.list_event_invitees("evt_uuid", count=5)

        assert len(invitees) == 1
        url = client.session.get.call_args[0][0]
        assert "/scheduled_events/evt_uuid/invitees" in url


# ---------------------------------------------------------------------------
# HubSpot
# ---------------------------------------------------------------------------


class TestHubSpotClient:
    @patch("goliath.integrations.hubspot.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.HUBSPOT_ACCESS_TOKEN = ""

        from goliath.integrations.hubspot import HubSpotClient

        with pytest.raises(RuntimeError, match="HUBSPOT_ACCESS_TOKEN"):
            HubSpotClient()

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "hs_tok"

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer hs_tok"

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_create_contact(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "ct_1", "properties": {"email": "j@x.com"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        client.create_contact(properties={"email": "j@x.com", "firstname": "Jane"})

        url = client.session.post.call_args[0][0]
        assert "/objects/contacts" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["properties"]["email"] == "j@x.com"

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_search_contacts(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": "ct_1"}]}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        results = client.search_contacts("jane@example.com")

        assert len(results) == 1
        url = client.session.post.call_args[0][0]
        assert "/contacts/search" in url

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_create_deal(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "deal_1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        client.create_deal(properties={"dealname": "Big Deal", "amount": "5000"})

        url = client.session.post.call_args[0][0]
        assert "/objects/deals" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["properties"]["dealname"] == "Big Deal"

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_list_companies(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"id": "co_1", "properties": {"name": "Acme"}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        companies = client.list_companies(limit=5)

        assert len(companies) == 1
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["limit"] == 5

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_delete_contact(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        client.delete_contact("ct_1")

        url = client.session.delete.call_args[0][0]
        assert "/objects/contacts/ct_1" in url

    @patch("goliath.integrations.hubspot.requests")
    @patch("goliath.integrations.hubspot.config")
    def test_update_contact(self, mock_config, mock_requests):
        mock_config.HUBSPOT_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "ct_1"}
        mock_requests.Session.return_value.patch.return_value = mock_resp

        from goliath.integrations.hubspot import HubSpotClient

        client = HubSpotClient()
        client.update_contact("ct_1", properties={"phone": "+1555"})

        url = client.session.patch.call_args[0][0]
        assert "/objects/contacts/ct_1" in url


# ---------------------------------------------------------------------------
# Salesforce
# ---------------------------------------------------------------------------


class TestSalesforceClient:
    @patch("goliath.integrations.salesforce.config")
    def test_missing_instance_url_raises(self, mock_config):
        mock_config.SALESFORCE_INSTANCE_URL = ""
        mock_config.SALESFORCE_ACCESS_TOKEN = "tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        from goliath.integrations.salesforce import SalesforceClient

        with pytest.raises(RuntimeError, match="SALESFORCE_INSTANCE_URL"):
            SalesforceClient()

    @patch("goliath.integrations.salesforce.config")
    def test_no_auth_raises(self, mock_config):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = ""
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        from goliath.integrations.salesforce import SalesforceClient

        with pytest.raises(RuntimeError, match="Salesforce credentials"):
            SalesforceClient()

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_token_init(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = "sf_tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        from goliath.integrations.salesforce import SalesforceClient

        client = SalesforceClient()
        client.session.headers.__setitem__.assert_any_call(
            "Authorization", "Bearer sf_tok"
        )

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_password_flow_auth(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = ""
        mock_config.SALESFORCE_CLIENT_ID = "cid"
        mock_config.SALESFORCE_CLIENT_SECRET = "csecret"
        mock_config.SALESFORCE_USERNAME = "user@sf.com"
        mock_config.SALESFORCE_PASSWORD = "passtoken"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pw_token"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.salesforce import SalesforceClient

        SalesforceClient()
        mock_requests.post.assert_called_once()
        call_data = mock_requests.post.call_args.kwargs.get(
            "data", mock_requests.post.call_args[1].get("data", {})
        )
        assert call_data["grant_type"] == "password"
        assert call_data["username"] == "user@sf.com"

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_query(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = "tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": [{"Name": "Acme"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.salesforce import SalesforceClient

        client = SalesforceClient()
        records = client.query("SELECT Name FROM Account LIMIT 1")

        assert len(records) == 1
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert "SELECT" in params["q"]

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_create_record(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = "tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "003xxx", "success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.salesforce import SalesforceClient

        client = SalesforceClient()
        client.create("Contact", {"FirstName": "Jane", "LastName": "Doe"})

        url = client.session.post.call_args[0][0]
        assert "/sobjects/Contact" in url

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_delete_record(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = "tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.salesforce import SalesforceClient

        client = SalesforceClient()
        client.delete("Contact", "003xxx")

        url = client.session.delete.call_args[0][0]
        assert "/sobjects/Contact/003xxx" in url

    @patch("goliath.integrations.salesforce.requests")
    @patch("goliath.integrations.salesforce.config")
    def test_base_url_includes_api_version(self, mock_config, mock_requests):
        mock_config.SALESFORCE_INSTANCE_URL = "https://na1.salesforce.com"
        mock_config.SALESFORCE_ACCESS_TOKEN = "tok"
        mock_config.SALESFORCE_CLIENT_ID = ""
        mock_config.SALESFORCE_CLIENT_SECRET = ""
        mock_config.SALESFORCE_USERNAME = ""
        mock_config.SALESFORCE_PASSWORD = ""

        from goliath.integrations.salesforce import SalesforceClient

        client = SalesforceClient()
        assert "v59.0" in client._base


# ---------------------------------------------------------------------------
# WordPress
# ---------------------------------------------------------------------------


class TestWordPressClient:
    @patch("goliath.integrations.wordpress.config")
    def test_missing_url_raises(self, mock_config):
        mock_config.WORDPRESS_URL = ""
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        from goliath.integrations.wordpress import WordPressClient

        with pytest.raises(RuntimeError, match="WORDPRESS_URL"):
            WordPressClient()

    @patch("goliath.integrations.wordpress.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = ""
        mock_config.WORDPRESS_APP_PASSWORD = ""

        from goliath.integrations.wordpress import WordPressClient

        with pytest.raises(RuntimeError, match="WORDPRESS_USERNAME"):
            WordPressClient()

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_auth_set(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "app_pass"

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        assert client.session.auth == ("admin", "app_pass")

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_create_post(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 42, "title": {"rendered": "Hello"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        client.create_post(title="Hello", content="<p>World</p>", status="publish")

        url = client.session.post.call_args[0][0]
        assert "/wp-json/wp/v2/posts" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["title"] == "Hello"
        assert payload["status"] == "publish"

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_list_posts(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": 1}, {"id": 2}]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        posts = client.list_posts(per_page=5)

        assert len(posts) == 2
        url = client.session.get.call_args[0][0]
        assert "/posts" in url

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_create_page(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 10, "title": {"rendered": "About"}}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        client.create_page(title="About", content="<p>About us</p>")

        url = client.session.post.call_args[0][0]
        assert "/pages" in url

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_delete_post(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 42, "status": "trash"}
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        client.delete_post(42)

        url = client.session.delete.call_args[0][0]
        assert "/posts/42" in url

    @patch("goliath.integrations.wordpress.requests")
    @patch("goliath.integrations.wordpress.config")
    def test_base_url_strips_trailing_slash(self, mock_config, mock_requests):
        mock_config.WORDPRESS_URL = "https://example.com/"
        mock_config.WORDPRESS_USERNAME = "admin"
        mock_config.WORDPRESS_APP_PASSWORD = "pass"

        from goliath.integrations.wordpress import WordPressClient

        client = WordPressClient()
        assert client._base == "https://example.com/wp-json/wp/v2"


# ---------------------------------------------------------------------------
# Webflow
# ---------------------------------------------------------------------------


class TestWebflowClient:
    @patch("goliath.integrations.webflow.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.WEBFLOW_ACCESS_TOKEN = ""

        from goliath.integrations.webflow import WebflowClient

        with pytest.raises(RuntimeError, match="WEBFLOW_ACCESS_TOKEN"):
            WebflowClient()

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "wf_tok"

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer wf_tok"

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_list_sites(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"sites": [{"id": "s1"}, {"id": "s2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        sites = client.list_sites()

        assert len(sites) == 2
        url = client.session.get.call_args[0][0]
        assert "/sites" in url

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_create_item(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "item_1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        client.create_item(
            collection_id="col_1",
            fields={"name": "New Post", "slug": "new-post"},
        )

        url = client.session.post.call_args[0][0]
        assert "/collections/col_1/items" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["fieldData"]["name"] == "New Post"

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_update_item(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "item_1"}
        mock_requests.Session.return_value.patch.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        client.update_item("col_1", "item_1", fields={"name": "Updated"})

        url = client.session.patch.call_args[0][0]
        assert "/collections/col_1/items/item_1" in url

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_publish_site(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"queued": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        client.publish_site("site_1")

        url = client.session.post.call_args[0][0]
        assert "/sites/site_1/publish" in url

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_delete_item(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        client.delete_item("col_1", "item_1")

        url = client.session.delete.call_args[0][0]
        assert "/collections/col_1/items/item_1" in url

    @patch("goliath.integrations.webflow.requests")
    @patch("goliath.integrations.webflow.config")
    def test_list_items(self, mock_config, mock_requests):
        mock_config.WEBFLOW_ACCESS_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"id": "i1"}, {"id": "i2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.webflow import WebflowClient

        client = WebflowClient()
        items = client.list_items("col_1", limit=50)

        assert len(items) == 2


# ---------------------------------------------------------------------------
# PayPal
# ---------------------------------------------------------------------------


class TestPayPalClient:
    @patch("goliath.integrations.paypal.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.PAYPAL_CLIENT_ID = ""
        mock_config.PAYPAL_CLIENT_SECRET = ""

        from goliath.integrations.paypal import PayPalClient

        with pytest.raises(RuntimeError, match="PAYPAL_CLIENT_ID"):
            PayPalClient()

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_sandbox_base_url(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        assert "sandbox" in client._base

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_live_base_url(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "false"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        assert "sandbox" not in client._base
        assert "api-m.paypal.com" in client._base

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_auth_uses_client_credentials(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        from goliath.integrations.paypal import PayPalClient

        PayPalClient()
        call_args = mock_requests.post.call_args
        assert call_args.kwargs.get("auth") == ("cid", "csecret") or call_args[1].get(
            "auth"
        ) == ("cid", "csecret")

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_create_order(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        order_resp = MagicMock()
        order_resp.json.return_value = {"id": "ORDER_1", "status": "CREATED"}
        order_resp.status_code = 201
        order_resp.content = b'{"id": "ORDER_1"}'
        mock_requests.Session.return_value.post.return_value = order_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        client.create_order(amount="29.99", currency="USD")

        call_args = client.session.post.call_args
        url = call_args[0][0]
        assert "/v2/checkout/orders" in url
        payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
        assert payload["purchase_units"][0]["amount"]["value"] == "29.99"
        assert payload["purchase_units"][0]["amount"]["currency_code"] == "USD"

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_capture_order(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        capture_resp = MagicMock()
        capture_resp.json.return_value = {"id": "ORDER_1", "status": "COMPLETED"}
        capture_resp.status_code = 201
        capture_resp.content = b'{"id": "ORDER_1"}'
        mock_requests.Session.return_value.post.return_value = capture_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        client.capture_order("ORDER_1")

        url = client.session.post.call_args[0][0]
        assert "/v2/checkout/orders/ORDER_1/capture" in url

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_create_payout(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        payout_resp = MagicMock()
        payout_resp.json.return_value = {"batch_header": {"payout_batch_id": "PB1"}}
        payout_resp.status_code = 201
        payout_resp.content = b'{"batch_header": {}}'
        mock_requests.Session.return_value.post.return_value = payout_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        client.create_payout(email="seller@example.com", amount="50.00", currency="USD")

        call_args = client.session.post.call_args
        url = call_args[0][0]
        assert "/v1/payments/payouts" in url
        payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
        assert payload["items"][0]["receiver"] == "seller@example.com"
        assert payload["items"][0]["amount"]["value"] == "50.00"

    @patch("goliath.integrations.paypal.requests")
    @patch("goliath.integrations.paypal.config")
    def test_refund_capture(self, mock_config, mock_requests):
        mock_config.PAYPAL_CLIENT_ID = "cid"
        mock_config.PAYPAL_CLIENT_SECRET = "csecret"
        mock_config.PAYPAL_SANDBOX = "true"

        auth_resp = MagicMock()
        auth_resp.json.return_value = {"access_token": "pp_tok"}
        mock_requests.post.return_value = auth_resp

        refund_resp = MagicMock()
        refund_resp.json.return_value = {"id": "REF_1", "status": "COMPLETED"}
        refund_resp.status_code = 201
        refund_resp.content = b'{"id": "REF_1"}'
        mock_requests.Session.return_value.post.return_value = refund_resp

        from goliath.integrations.paypal import PayPalClient

        client = PayPalClient()
        client.refund_capture("CAP_1", amount="10.00", currency="EUR")

        url = client.session.post.call_args[0][0]
        assert "/v2/payments/captures/CAP_1/refund" in url
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["amount"]["value"] == "10.00"
        assert payload["amount"]["currency_code"] == "EUR"
