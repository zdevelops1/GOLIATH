"""Tests for batch 5 integrations: Vercel, Sentry, Datadog, PagerDuty,
Mixpanel, Segment, Algolia, Contentful, Plaid, ClickUp."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Vercel
# ---------------------------------------------------------------------------


class TestVercelClient:
    @patch("goliath.integrations.vercel.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.VERCEL_ACCESS_TOKEN = ""

        from goliath.integrations.vercel import VercelClient

        with pytest.raises(RuntimeError, match="VERCEL_ACCESS_TOKEN"):
            VercelClient()

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "test-tok"
        mock_config.VERCEL_TEAM_ID = ""

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer test-tok"

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_list_projects(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "tok"
        mock_config.VERCEL_TEAM_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "projects": [{"id": "prj_1", "name": "my-app"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        projects = client.list_projects()

        assert len(projects) == 1
        assert projects[0]["name"] == "my-app"

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_get_deployment(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "tok"
        mock_config.VERCEL_TEAM_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "dpl_1", "state": "READY"}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        deploy = client.get_deployment("dpl_1")

        assert deploy["state"] == "READY"
        url = client.session.get.call_args[0][0]
        assert "/v13/deployments/dpl_1" in url

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_create_deployment(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "tok"
        mock_config.VERCEL_TEAM_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "dpl_new", "state": "BUILDING"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        deploy = client.create_deployment(
            name="my-app",
            git_source={"type": "github", "repo": "user/repo", "ref": "main"},
        )

        assert deploy["state"] == "BUILDING"

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_list_domains(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "tok"
        mock_config.VERCEL_TEAM_ID = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "domains": [{"name": "app.example.com"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        domains = client.list_domains("prj_1")

        assert len(domains) == 1
        assert domains[0]["name"] == "app.example.com"

    @patch("goliath.integrations.vercel.requests")
    @patch("goliath.integrations.vercel.config")
    def test_team_params_added(self, mock_config, mock_requests):
        mock_config.VERCEL_ACCESS_TOKEN = "tok"
        mock_config.VERCEL_TEAM_ID = "team_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"projects": []}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.vercel import VercelClient

        client = VercelClient()
        client.list_projects()

        call_kwargs = client.session.get.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        assert params.get("teamId") == "team_abc"


# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------


class TestSentryClient:
    @patch("goliath.integrations.sentry.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.SENTRY_AUTH_TOKEN = ""
        mock_config.SENTRY_ORG = "my-org"
        mock_config.SENTRY_BASE_URL = ""

        from goliath.integrations.sentry import SentryClient

        with pytest.raises(RuntimeError, match="SENTRY_AUTH_TOKEN"):
            SentryClient()

    @patch("goliath.integrations.sentry.config")
    def test_missing_org_raises(self, mock_config):
        mock_config.SENTRY_AUTH_TOKEN = "tok"
        mock_config.SENTRY_ORG = ""
        mock_config.SENTRY_BASE_URL = ""

        from goliath.integrations.sentry import SentryClient

        with pytest.raises(RuntimeError, match="SENTRY_ORG"):
            SentryClient()

    @patch("goliath.integrations.sentry.requests")
    @patch("goliath.integrations.sentry.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.SENTRY_AUTH_TOKEN = "sntrys_test"
        mock_config.SENTRY_ORG = "my-org"
        mock_config.SENTRY_BASE_URL = ""

        from goliath.integrations.sentry import SentryClient

        client = SentryClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer sntrys_test"

    @patch("goliath.integrations.sentry.requests")
    @patch("goliath.integrations.sentry.config")
    def test_list_projects(self, mock_config, mock_requests):
        mock_config.SENTRY_AUTH_TOKEN = "tok"
        mock_config.SENTRY_ORG = "my-org"
        mock_config.SENTRY_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"slug": "my-project", "name": "My Project"}]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.sentry import SentryClient

        client = SentryClient()
        projects = client.list_projects()

        assert len(projects) == 1
        assert projects[0]["slug"] == "my-project"
        url = client.session.get.call_args[0][0]
        assert "/organizations/my-org/projects/" in url

    @patch("goliath.integrations.sentry.requests")
    @patch("goliath.integrations.sentry.config")
    def test_list_issues(self, mock_config, mock_requests):
        mock_config.SENTRY_AUTH_TOKEN = "tok"
        mock_config.SENTRY_ORG = "my-org"
        mock_config.SENTRY_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"id": "123", "title": "TypeError", "status": "unresolved"}
        ]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.sentry import SentryClient

        client = SentryClient()
        issues = client.list_issues("my-project")

        assert len(issues) == 1
        assert issues[0]["title"] == "TypeError"

    @patch("goliath.integrations.sentry.requests")
    @patch("goliath.integrations.sentry.config")
    def test_update_issue(self, mock_config, mock_requests):
        mock_config.SENTRY_AUTH_TOKEN = "tok"
        mock_config.SENTRY_ORG = "my-org"
        mock_config.SENTRY_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "123", "status": "resolved"}
        mock_requests.Session.return_value.put.return_value = mock_resp

        from goliath.integrations.sentry import SentryClient

        client = SentryClient()
        result = client.update_issue("123", status="resolved")

        assert result["status"] == "resolved"


# ---------------------------------------------------------------------------
# Datadog
# ---------------------------------------------------------------------------


class TestDatadogClient:
    @patch("goliath.integrations.datadog.config")
    def test_missing_api_key_raises(self, mock_config):
        mock_config.DATADOG_API_KEY = ""
        mock_config.DATADOG_APP_KEY = ""
        mock_config.DATADOG_SITE = ""

        from goliath.integrations.datadog import DatadogClient

        with pytest.raises(RuntimeError, match="DATADOG_API_KEY"):
            DatadogClient()

    @patch("goliath.integrations.datadog.requests")
    @patch("goliath.integrations.datadog.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.DATADOG_API_KEY = "dd_api_test"
        mock_config.DATADOG_APP_KEY = "dd_app_test"
        mock_config.DATADOG_SITE = ""

        from goliath.integrations.datadog import DatadogClient

        client = DatadogClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["DD-API-KEY"] == "dd_api_test"
        assert call_kwargs["DD-APPLICATION-KEY"] == "dd_app_test"

    @patch("goliath.integrations.datadog.requests")
    @patch("goliath.integrations.datadog.config")
    def test_submit_metric(self, mock_config, mock_requests):
        mock_config.DATADOG_API_KEY = "key"
        mock_config.DATADOG_APP_KEY = ""
        mock_config.DATADOG_SITE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "ok"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.datadog import DatadogClient

        client = DatadogClient()
        result = client.submit_metric("cpu.usage", value=85.5, tags=["env:prod"])

        assert result["status"] == "ok"
        url = client.session.post.call_args[0][0]
        assert "/v2/series" in url

    @patch("goliath.integrations.datadog.requests")
    @patch("goliath.integrations.datadog.config")
    def test_list_monitors(self, mock_config, mock_requests):
        mock_config.DATADOG_API_KEY = "key"
        mock_config.DATADOG_APP_KEY = "app"
        mock_config.DATADOG_SITE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": 1, "name": "High CPU"}]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.datadog import DatadogClient

        client = DatadogClient()
        monitors = client.list_monitors()

        assert len(monitors) == 1
        assert monitors[0]["name"] == "High CPU"

    @patch("goliath.integrations.datadog.requests")
    @patch("goliath.integrations.datadog.config")
    def test_create_event(self, mock_config, mock_requests):
        mock_config.DATADOG_API_KEY = "key"
        mock_config.DATADOG_APP_KEY = ""
        mock_config.DATADOG_SITE = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "event": {"id": 42, "title": "Deploy"}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.datadog import DatadogClient

        client = DatadogClient()
        result = client.create_event(
            title="Deploy", text="Deployed v2.1", tags=["env:prod"]
        )

        assert result["id"] == 42

    @patch("goliath.integrations.datadog.requests")
    @patch("goliath.integrations.datadog.config")
    def test_custom_site(self, mock_config, mock_requests):
        mock_config.DATADOG_API_KEY = "key"
        mock_config.DATADOG_APP_KEY = ""
        mock_config.DATADOG_SITE = "datadoghq.eu"

        from goliath.integrations.datadog import DatadogClient

        client = DatadogClient()
        assert "datadoghq.eu" in client.base_url


# ---------------------------------------------------------------------------
# PagerDuty
# ---------------------------------------------------------------------------


class TestPagerDutyClient:
    @patch("goliath.integrations.pagerduty.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.PAGERDUTY_API_KEY = ""
        mock_config.PAGERDUTY_FROM_EMAIL = ""

        from goliath.integrations.pagerduty import PagerDutyClient

        with pytest.raises(RuntimeError, match="PAGERDUTY_API_KEY"):
            PagerDutyClient()

    @patch("goliath.integrations.pagerduty.requests")
    @patch("goliath.integrations.pagerduty.config")
    def test_auth_header(self, mock_config, mock_requests):
        mock_config.PAGERDUTY_API_KEY = "pd_test_key"
        mock_config.PAGERDUTY_FROM_EMAIL = "me@example.com"

        from goliath.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Token token=pd_test_key"

    @patch("goliath.integrations.pagerduty.requests")
    @patch("goliath.integrations.pagerduty.config")
    def test_list_incidents(self, mock_config, mock_requests):
        mock_config.PAGERDUTY_API_KEY = "key"
        mock_config.PAGERDUTY_FROM_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "incidents": [{"id": "P123", "status": "triggered"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient()
        incidents = client.list_incidents()

        assert len(incidents) == 1
        assert incidents[0]["status"] == "triggered"

    @patch("goliath.integrations.pagerduty.requests")
    @patch("goliath.integrations.pagerduty.config")
    def test_create_incident(self, mock_config, mock_requests):
        mock_config.PAGERDUTY_API_KEY = "key"
        mock_config.PAGERDUTY_FROM_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "incident": {"id": "P456", "title": "DB Down", "status": "triggered"}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient()
        result = client.create_incident(
            title="DB Down", service_id="PSVC1", urgency="high"
        )

        assert result["title"] == "DB Down"

    @patch("goliath.integrations.pagerduty.requests")
    @patch("goliath.integrations.pagerduty.config")
    def test_list_services(self, mock_config, mock_requests):
        mock_config.PAGERDUTY_API_KEY = "key"
        mock_config.PAGERDUTY_FROM_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "services": [{"id": "PSVC1", "name": "Web App"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient()
        services = client.list_services()

        assert services[0]["name"] == "Web App"

    @patch("goliath.integrations.pagerduty.requests")
    @patch("goliath.integrations.pagerduty.config")
    def test_list_oncalls(self, mock_config, mock_requests):
        mock_config.PAGERDUTY_API_KEY = "key"
        mock_config.PAGERDUTY_FROM_EMAIL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "oncalls": [{"user": {"name": "Alice"}, "schedule": {"id": "SCH1"}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.pagerduty import PagerDutyClient

        client = PagerDutyClient()
        oncalls = client.list_oncalls()

        assert oncalls[0]["user"]["name"] == "Alice"


# ---------------------------------------------------------------------------
# Mixpanel
# ---------------------------------------------------------------------------


class TestMixpanelClient:
    @patch("goliath.integrations.mixpanel.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.MIXPANEL_PROJECT_TOKEN = ""

        from goliath.integrations.mixpanel import MixpanelClient

        with pytest.raises(RuntimeError, match="MIXPANEL_PROJECT_TOKEN"):
            MixpanelClient()

    @patch("goliath.integrations.mixpanel.requests")
    @patch("goliath.integrations.mixpanel.config")
    def test_track_event(self, mock_config, mock_requests):
        mock_config.MIXPANEL_PROJECT_TOKEN = "mp_tok"
        mock_config.MIXPANEL_PROJECT_ID = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_USER = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = 1
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.mixpanel import MixpanelClient

        client = MixpanelClient()
        result = client.track(
            distinct_id="user-1", event="Purchase", properties={"amount": 42}
        )

        assert result == 1
        url = client.session.post.call_args[0][0]
        assert "/track" in url

    @patch("goliath.integrations.mixpanel.requests")
    @patch("goliath.integrations.mixpanel.config")
    def test_track_includes_token(self, mock_config, mock_requests):
        mock_config.MIXPANEL_PROJECT_TOKEN = "mp_tok"
        mock_config.MIXPANEL_PROJECT_ID = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_USER = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = 1
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.mixpanel import MixpanelClient

        client = MixpanelClient()
        client.track(distinct_id="u1", event="Click")

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", [])
        )
        assert payload[0]["properties"]["token"] == "mp_tok"

    @patch("goliath.integrations.mixpanel.requests")
    @patch("goliath.integrations.mixpanel.config")
    def test_set_user(self, mock_config, mock_requests):
        mock_config.MIXPANEL_PROJECT_TOKEN = "mp_tok"
        mock_config.MIXPANEL_PROJECT_ID = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_USER = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = 1
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.mixpanel import MixpanelClient

        client = MixpanelClient()
        result = client.set_user("user-1", {"$name": "Alice"})

        assert result == 1
        url = client.session.post.call_args[0][0]
        assert "/engage" in url

    @patch("goliath.integrations.mixpanel.requests")
    @patch("goliath.integrations.mixpanel.config")
    def test_sa_auth_missing_raises(self, mock_config, mock_requests):
        mock_config.MIXPANEL_PROJECT_TOKEN = "mp_tok"
        mock_config.MIXPANEL_PROJECT_ID = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_USER = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_SECRET = ""

        from goliath.integrations.mixpanel import MixpanelClient

        client = MixpanelClient()
        with pytest.raises(RuntimeError, match="Service account"):
            client.top_events()

    @patch("goliath.integrations.mixpanel.requests")
    @patch("goliath.integrations.mixpanel.config")
    def test_track_batch(self, mock_config, mock_requests):
        mock_config.MIXPANEL_PROJECT_TOKEN = "mp_tok"
        mock_config.MIXPANEL_PROJECT_ID = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_USER = ""
        mock_config.MIXPANEL_SERVICE_ACCOUNT_SECRET = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = 1
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.mixpanel import MixpanelClient

        client = MixpanelClient()
        events = [
            {"event": "View", "properties": {"distinct_id": "u1"}},
            {"event": "Click", "properties": {"distinct_id": "u1"}},
        ]
        result = client.track_batch(events)

        assert result == 1


# ---------------------------------------------------------------------------
# Segment
# ---------------------------------------------------------------------------


class TestSegmentClient:
    @patch("goliath.integrations.segment.config")
    def test_missing_write_key_raises(self, mock_config):
        mock_config.SEGMENT_WRITE_KEY = ""

        from goliath.integrations.segment import SegmentClient

        with pytest.raises(RuntimeError, match="SEGMENT_WRITE_KEY"):
            SegmentClient()

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_auth_header_basic(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert "Basic" in call_kwargs["Authorization"]

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_identify(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        result = client.identify(user_id="u1", traits={"name": "Alice"})

        assert result["success"] is True
        url = client.session.post.call_args[0][0]
        assert "/identify" in url

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_track(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        result = client.track(
            user_id="u1", event="Purchase", properties={"amount": 50}
        )

        assert result["success"] is True
        url = client.session.post.call_args[0][0]
        assert "/track" in url

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_page(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        result = client.page(user_id="u1", name="Home")

        assert result["success"] is True

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_group(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        result = client.group(
            user_id="u1", group_id="g1", traits={"name": "Acme"}
        )

        assert result["success"] is True
        url = client.session.post.call_args[0][0]
        assert "/group" in url

    @patch("goliath.integrations.segment.requests")
    @patch("goliath.integrations.segment.config")
    def test_batch(self, mock_config, mock_requests):
        mock_config.SEGMENT_WRITE_KEY = "seg_key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.segment import SegmentClient

        client = SegmentClient()
        result = client.batch([
            {"type": "identify", "userId": "u1", "traits": {"name": "Bob"}},
            {"type": "track", "userId": "u1", "event": "Login"},
        ])

        assert result["success"] is True
        url = client.session.post.call_args[0][0]
        assert "/batch" in url


# ---------------------------------------------------------------------------
# Algolia
# ---------------------------------------------------------------------------


class TestAlgoliaClient:
    @patch("goliath.integrations.algolia.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.ALGOLIA_APP_ID = ""
        mock_config.ALGOLIA_API_KEY = ""

        from goliath.integrations.algolia import AlgoliaClient

        with pytest.raises(RuntimeError, match="ALGOLIA_APP_ID"):
            AlgoliaClient()

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "APP123"
        mock_config.ALGOLIA_API_KEY = "admin_key"

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-Algolia-Application-Id"] == "APP123"
        assert call_kwargs["X-Algolia-API-Key"] == "admin_key"

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "APP123"
        mock_config.ALGOLIA_API_KEY = "key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "hits": [{"objectID": "1", "name": "Laptop"}],
            "nbHits": 1,
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        results = client.search("products", query="laptop")

        assert results["nbHits"] == 1
        assert results["hits"][0]["name"] == "Laptop"

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_save_objects(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "APP123"
        mock_config.ALGOLIA_API_KEY = "key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"taskID": 99, "objectIDs": ["1", "2"]}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        result = client.save_objects("products", [
            {"objectID": "1", "name": "Laptop"},
            {"objectID": "2", "name": "Mouse"},
        ])

        assert result["taskID"] == 99

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_get_object(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "APP123"
        mock_config.ALGOLIA_API_KEY = "key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"objectID": "1", "name": "Laptop"}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        obj = client.get_object("products", "1")

        assert obj["name"] == "Laptop"
        url = client.session.get.call_args[0][0]
        assert "/1/indexes/products/1" in url

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_list_indices(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "APP123"
        mock_config.ALGOLIA_API_KEY = "key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"name": "products", "entries": 100}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        indices = client.list_indices()

        assert len(indices) == 1
        assert indices[0]["name"] == "products"

    @patch("goliath.integrations.algolia.requests")
    @patch("goliath.integrations.algolia.config")
    def test_base_url_uses_app_id(self, mock_config, mock_requests):
        mock_config.ALGOLIA_APP_ID = "MYAPP"
        mock_config.ALGOLIA_API_KEY = "key"

        from goliath.integrations.algolia import AlgoliaClient

        client = AlgoliaClient()
        assert client.base_url == "https://MYAPP.algolia.net"


# ---------------------------------------------------------------------------
# Contentful
# ---------------------------------------------------------------------------


class TestContentfulClient:
    @patch("goliath.integrations.contentful.config")
    def test_missing_space_id_raises(self, mock_config):
        mock_config.CONTENTFUL_SPACE_ID = ""
        mock_config.CONTENTFUL_ACCESS_TOKEN = "tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        from goliath.integrations.contentful import ContentfulClient

        with pytest.raises(RuntimeError, match="CONTENTFUL_SPACE_ID"):
            ContentfulClient()

    @patch("goliath.integrations.contentful.config")
    def test_missing_access_token_raises(self, mock_config):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = ""
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        from goliath.integrations.contentful import ContentfulClient

        with pytest.raises(RuntimeError, match="CONTENTFUL_ACCESS_TOKEN"):
            ContentfulClient()

    @patch("goliath.integrations.contentful.requests")
    @patch("goliath.integrations.contentful.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = "cda_tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        from goliath.integrations.contentful import ContentfulClient

        client = ContentfulClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer cda_tok"

    @patch("goliath.integrations.contentful.requests")
    @patch("goliath.integrations.contentful.config")
    def test_list_entries(self, mock_config, mock_requests):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = "tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"sys": {"id": "entry1"}, "fields": {"title": {"en-US": "Hello"}}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.contentful import ContentfulClient

        client = ContentfulClient()
        entries = client.list_entries()

        assert len(entries) == 1
        url = client.session.get.call_args[0][0]
        assert "/spaces/space123/entries" in url

    @patch("goliath.integrations.contentful.requests")
    @patch("goliath.integrations.contentful.config")
    def test_list_content_types(self, mock_config, mock_requests):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = "tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"sys": {"id": "blogPost"}, "name": "Blog Post"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.contentful import ContentfulClient

        client = ContentfulClient()
        types = client.list_content_types()

        assert types[0]["name"] == "Blog Post"

    @patch("goliath.integrations.contentful.requests")
    @patch("goliath.integrations.contentful.config")
    def test_create_entry_requires_cma(self, mock_config, mock_requests):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = "tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        from goliath.integrations.contentful import ContentfulClient

        client = ContentfulClient()
        with pytest.raises(RuntimeError, match="CONTENTFUL_MANAGEMENT_TOKEN"):
            client.create_entry("blogPost", fields={"title": {"en-US": "Hi"}})

    @patch("goliath.integrations.contentful.requests")
    @patch("goliath.integrations.contentful.config")
    def test_list_assets(self, mock_config, mock_requests):
        mock_config.CONTENTFUL_SPACE_ID = "space123"
        mock_config.CONTENTFUL_ACCESS_TOKEN = "tok"
        mock_config.CONTENTFUL_MANAGEMENT_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"sys": {"id": "asset1"}, "fields": {"title": {"en-US": "Logo"}}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.contentful import ContentfulClient

        client = ContentfulClient()
        assets = client.list_assets()

        assert len(assets) == 1


# ---------------------------------------------------------------------------
# Plaid
# ---------------------------------------------------------------------------


class TestPlaidClient:
    @patch("goliath.integrations.plaid.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.PLAID_CLIENT_ID = ""
        mock_config.PLAID_SECRET = ""
        mock_config.PLAID_ENV = "sandbox"

        from goliath.integrations.plaid import PlaidClient

        with pytest.raises(RuntimeError, match="PLAID_CLIENT_ID"):
            PlaidClient()

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_sandbox_base_url(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "client_id"
        mock_config.PLAID_SECRET = "secret"
        mock_config.PLAID_ENV = "sandbox"

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        assert "sandbox.plaid.com" in client.base_url

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_create_link_token(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "cid"
        mock_config.PLAID_SECRET = "sec"
        mock_config.PLAID_ENV = "sandbox"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "link_token": "link-sandbox-xxx",
            "expiration": "2025-12-31",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        result = client.create_link_token(user_id="u1")

        assert result["link_token"] == "link-sandbox-xxx"
        url = client.session.post.call_args[0][0]
        assert "/link/token/create" in url

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_exchange_public_token(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "cid"
        mock_config.PLAID_SECRET = "sec"
        mock_config.PLAID_ENV = "sandbox"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "access-sandbox-xxx",
            "item_id": "item-1",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        result = client.exchange_public_token("public-sandbox-xxx")

        assert result["access_token"] == "access-sandbox-xxx"

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_get_balance(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "cid"
        mock_config.PLAID_SECRET = "sec"
        mock_config.PLAID_ENV = "sandbox"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "accounts": [
                {"account_id": "acc1", "balances": {"current": 1000.00}}
            ]
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        accounts = client.get_balance(access_token="access-tok")

        assert len(accounts) == 1
        assert accounts[0]["balances"]["current"] == 1000.00

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_get_transactions(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "cid"
        mock_config.PLAID_SECRET = "sec"
        mock_config.PLAID_ENV = "sandbox"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "transactions": [
                {"transaction_id": "tx1", "amount": 42.00, "name": "Coffee"}
            ],
            "total_transactions": 1,
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        result = client.get_transactions(
            access_token="tok", start_date="2025-01-01", end_date="2025-01-31"
        )

        assert result["total_transactions"] == 1
        assert result["transactions"][0]["name"] == "Coffee"

    @patch("goliath.integrations.plaid.requests")
    @patch("goliath.integrations.plaid.config")
    def test_auth_payload_included(self, mock_config, mock_requests):
        mock_config.PLAID_CLIENT_ID = "my_client"
        mock_config.PLAID_SECRET = "my_secret"
        mock_config.PLAID_ENV = "sandbox"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"accounts": []}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.plaid import PlaidClient

        client = PlaidClient()
        client.get_accounts(access_token="tok")

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["client_id"] == "my_client"
        assert payload["secret"] == "my_secret"


# ---------------------------------------------------------------------------
# ClickUp
# ---------------------------------------------------------------------------


class TestClickUpClient:
    @patch("goliath.integrations.clickup.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.CLICKUP_API_TOKEN = ""

        from goliath.integrations.clickup import ClickUpClient

        with pytest.raises(RuntimeError, match="CLICKUP_API_TOKEN"):
            ClickUpClient()

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_auth_header(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "pk_test123"

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "pk_test123"

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_list_teams(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "teams": [{"id": "t1", "name": "My Workspace"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        teams = client.list_teams()

        assert len(teams) == 1
        assert teams[0]["name"] == "My Workspace"

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_list_tasks(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "tasks": [{"id": "task1", "name": "Fix bug", "status": {"status": "open"}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        tasks = client.list_tasks("list1")

        assert len(tasks) == 1
        assert tasks[0]["name"] == "Fix bug"

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_create_task(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": "task_new", "name": "New Task", "status": {"status": "open"}
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        task = client.create_task("list1", name="New Task", description="Details")

        assert task["name"] == "New Task"
        url = client.session.post.call_args[0][0]
        assert "/list/list1/task" in url

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_add_comment(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "comment1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        result = client.add_comment("task1", comment_text="Looking into it.")

        assert result["id"] == "comment1"
        url = client.session.post.call_args[0][0]
        assert "/task/task1/comment" in url

    @patch("goliath.integrations.clickup.requests")
    @patch("goliath.integrations.clickup.config")
    def test_list_spaces(self, mock_config, mock_requests):
        mock_config.CLICKUP_API_TOKEN = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "spaces": [{"id": "s1", "name": "Engineering"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.clickup import ClickUpClient

        client = ClickUpClient()
        spaces = client.list_spaces("t1")

        assert spaces[0]["name"] == "Engineering"
