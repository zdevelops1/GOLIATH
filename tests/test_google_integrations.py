"""Tests for Google Workspace integrations: Sheets, Drive, Calendar, Docs.

All four share the service account pattern, which we mock via google.oauth2.
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


def _mock_google_auth():
    """Create mocks for google.auth and google.oauth2.service_account."""
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.token = "fake-access-token"

    mock_sa = MagicMock()
    mock_sa.Credentials.from_service_account_file.return_value = mock_creds

    mock_request = MagicMock()
    return mock_creds, mock_sa, mock_request


# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

class TestSheetsClient:

    @patch("goliath.integrations.sheets.config")
    def test_no_credentials_raises(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""
        mock_config.GOOGLE_SHEETS_API_KEY = ""

        from goliath.integrations.sheets import SheetsClient
        with pytest.raises(RuntimeError, match="No Google Sheets credentials"):
            SheetsClient()

    @patch("goliath.integrations.sheets.config")
    def test_api_key_only_init(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""
        mock_config.GOOGLE_SHEETS_API_KEY = "AIza-test"

        from goliath.integrations.sheets import SheetsClient
        client = SheetsClient()
        assert client._api_key == "AIza-test"
        assert client._credentials is None

    @patch("goliath.integrations.sheets.config")
    def test_api_key_get_values(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""
        mock_config.GOOGLE_SHEETS_API_KEY = "AIza-test"

        from goliath.integrations.sheets import SheetsClient
        client = SheetsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"values": [["A", "B"], ["1", "2"]]}
        client.session.get = MagicMock(return_value=mock_resp)

        result = client.get_values("spreadsheet_1", "Sheet1!A1:B2")

        assert result == [["A", "B"], ["1", "2"]]
        call_kwargs = client.session.get.call_args.kwargs
        assert call_kwargs["headers"]["X-Goog-Api-Key"] == "AIza-test"

    @patch("goliath.integrations.sheets.config")
    def test_api_key_write_requires_service_account(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""
        mock_config.GOOGLE_SHEETS_API_KEY = "AIza-test"

        from goliath.integrations.sheets import SheetsClient
        client = SheetsClient()

        with pytest.raises(RuntimeError, match="requires a service account"):
            client.update_values("id", "Sheet1!A1", [["val"]])

        with pytest.raises(RuntimeError, match="requires a service account"):
            client.append_values("id", "Sheet1", [["val"]])

        with pytest.raises(RuntimeError, match="requires a service account"):
            client.clear_values("id", "Sheet1!A1:B2")

        with pytest.raises(RuntimeError, match="requires a service account"):
            client.create_spreadsheet("Title")

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.sheets.config")
    def test_service_account_update_values(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/path/to/sa.json"
        mock_config.GOOGLE_SHEETS_API_KEY = ""

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.token = "sa-token"
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.sheets import SheetsClient
        client = SheetsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"updatedCells": 4}
        client.session.put = MagicMock(return_value=mock_resp)

        result = client.update_values("sid", "Sheet1!A1", [["a", "b"]])
        assert result["updatedCells"] == 4

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.sheets.config")
    def test_service_account_create_spreadsheet(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/path/to/sa.json"
        mock_config.GOOGLE_SHEETS_API_KEY = ""

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.token = "sa-token"
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.sheets import SheetsClient
        client = SheetsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"spreadsheetId": "new_id"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_spreadsheet("My Sheet")
        assert result["spreadsheetId"] == "new_id"
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["properties"]["title"] == "My Sheet"


# ---------------------------------------------------------------------------
# Google Drive
# ---------------------------------------------------------------------------

class TestDriveClient:

    @patch("goliath.integrations.drive.config")
    def test_no_service_account_raises(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.drive import DriveClient
        with pytest.raises(RuntimeError, match="GOOGLE_SERVICE_ACCOUNT_FILE"):
            DriveClient()

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.drive.config")
    def test_list_files(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.drive import DriveClient
        client = DriveClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"files": [{"id": "f1", "name": "doc.pdf"}]}
        client.session.get = MagicMock(return_value=mock_resp)

        files = client.list_files(query="mimeType='application/pdf'")
        assert len(files) == 1
        assert files[0]["name"] == "doc.pdf"
        call_kwargs = client.session.get.call_args.kwargs
        assert call_kwargs["params"]["q"] == "mimeType='application/pdf'"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.drive.config")
    def test_create_folder(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.drive import DriveClient
        client = DriveClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "folder_1", "name": "Assets"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_folder("Assets", parent_id="parent_1")
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["mimeType"] == "application/vnd.google-apps.folder"
        assert payload["parents"] == ["parent_1"]

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.drive.config")
    def test_share_file(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.drive import DriveClient
        client = DriveClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "perm_1"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.share_file("f1", email="user@example.com", role="writer")
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["emailAddress"] == "user@example.com"
        assert payload["role"] == "writer"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.drive.config")
    def test_upload_file_not_found(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.drive import DriveClient
        client = DriveClient()
        with pytest.raises(FileNotFoundError):
            client.upload_file("/nonexistent/file.pdf")

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.drive.config")
    def test_delete_file(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.drive import DriveClient
        client = DriveClient()

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        client.session.delete = MagicMock(return_value=mock_resp)

        client.delete_file("f1")  # should not raise
        client.session.delete.assert_called_once()


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class TestCalendarClient:

    @patch("goliath.integrations.calendar.config")
    def test_no_service_account_raises(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.calendar import CalendarClient
        with pytest.raises(RuntimeError, match="GOOGLE_SERVICE_ACCOUNT_FILE"):
            CalendarClient()

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.calendar.config")
    def test_list_events(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.calendar import CalendarClient
        client = CalendarClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"id": "e1", "summary": "Standup"}]}
        client.session.get = MagicMock(return_value=mock_resp)

        events = client.list_events()
        assert len(events) == 1
        assert events[0]["summary"] == "Standup"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.calendar.config")
    def test_create_event(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.calendar import CalendarClient
        client = CalendarClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "e2", "summary": "Meeting"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_event(
            summary="Meeting",
            start="2025-06-01T09:00:00",
            end="2025-06-01T10:00:00",
            timezone="America/New_York",
            attendees=["alice@example.com"],
        )
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["summary"] == "Meeting"
        assert payload["start"]["timeZone"] == "America/New_York"
        assert payload["attendees"] == [{"email": "alice@example.com"}]

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.calendar.config")
    def test_update_event(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.calendar import CalendarClient
        client = CalendarClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "e1", "summary": "Updated"}
        client.session.patch = MagicMock(return_value=mock_resp)

        result = client.update_event("e1", summary="Updated", location="Room 42")
        payload = client.session.patch.call_args.kwargs["json"]
        assert payload["summary"] == "Updated"
        assert payload["location"] == "Room 42"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.calendar.config")
    def test_delete_event(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.calendar import CalendarClient
        client = CalendarClient()

        mock_resp = MagicMock()
        client.session.delete = MagicMock(return_value=mock_resp)

        client.delete_event("e1")
        url = client.session.delete.call_args[0][0]
        assert "e1" in url


# ---------------------------------------------------------------------------
# Google Docs
# ---------------------------------------------------------------------------

class TestDocsClient:

    @patch("goliath.integrations.docs.config")
    def test_no_service_account_raises(self, mock_config):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = ""

        from goliath.integrations.docs import DocsClient
        with pytest.raises(RuntimeError, match="GOOGLE_SERVICE_ACCOUNT_FILE"):
            DocsClient()

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.docs.config")
    def test_get_document(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.docs import DocsClient
        client = DocsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"documentId": "d1", "title": "Notes"}
        client.session.get = MagicMock(return_value=mock_resp)

        result = client.get_document("d1")
        assert result["title"] == "Notes"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.docs.config")
    def test_create_document(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.docs import DocsClient
        client = DocsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"documentId": "d2", "title": "New Doc"}
        client.session.post = MagicMock(return_value=mock_resp)

        result = client.create_document("New Doc")
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["title"] == "New Doc"

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.docs.config")
    def test_batch_update(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.docs import DocsClient
        client = DocsClient()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"replies": [{}]}
        client.session.post = MagicMock(return_value=mock_resp)

        reqs = [{"insertText": {"location": {"index": 1}, "text": "Hello\n"}}]
        result = client.batch_update("d1", requests=reqs)

        url = client.session.post.call_args[0][0]
        assert "d1:batchUpdate" in url
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["requests"] == reqs

    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    @patch("goliath.integrations.docs.config")
    def test_append_text(self, mock_config, mock_request, mock_from_sa):
        mock_config.GOOGLE_SERVICE_ACCOUNT_FILE = "/sa.json"
        mock_creds = MagicMock(valid=True, expired=False, token="tok")
        mock_from_sa.return_value = mock_creds

        from goliath.integrations.docs import DocsClient
        client = DocsClient()

        # Mock get_document (to find end index) and batch_update
        get_resp = MagicMock()
        get_resp.json.return_value = {
            "body": {"content": [{"endIndex": 50}]},
        }
        post_resp = MagicMock()
        post_resp.json.return_value = {"replies": [{}]}
        client.session.get = MagicMock(return_value=get_resp)
        client.session.post = MagicMock(return_value=post_resp)

        client.append_text("d1", "\nNew paragraph")

        # Verify the insertText uses the correct end index (50 - 1 = 49)
        payload = client.session.post.call_args.kwargs["json"]
        insert_req = payload["requests"][0]["insertText"]
        assert insert_req["location"]["index"] == 49
        assert insert_req["text"] == "\nNew paragraph"
