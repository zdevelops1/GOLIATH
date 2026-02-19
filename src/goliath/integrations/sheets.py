"""
Google Sheets Integration — read, write, and manage spreadsheet data.

SETUP INSTRUCTIONS
==================

Two authentication modes are supported:

Option A — API Key (read-only access to public spreadsheets):
  1. Go to https://console.cloud.google.com/apis/credentials
  2. Click "Create Credentials" > "API key".
  3. (Recommended) Restrict the key to the Google Sheets API.
  4. Add it to your .env:
       GOOGLE_SHEETS_API_KEY=AIza...

Option B — Service Account (full read/write access):
  1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
  2. Create a service account and download its JSON key file.
  3. Enable the Google Sheets API for your project:
       https://console.cloud.google.com/apis/library/sheets.googleapis.com
  4. Share each target spreadsheet with the service account email
     (the email looks like: name@project-id.iam.gserviceaccount.com).
  5. Add the path to your .env:
       GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

Both can be set simultaneously — the client prefers the service account
for write operations and falls back to the API key for reads.

Usage:
    from goliath.integrations.sheets import SheetsClient

    sheets = SheetsClient()

    # Read values from a range
    data = sheets.get_values("SPREADSHEET_ID", "Sheet1!A1:D10")

    # Update values
    sheets.update_values("SPREADSHEET_ID", "Sheet1!A1", [["Name", "Age"], ["Alice", 30]])

    # Append rows
    sheets.append_values("SPREADSHEET_ID", "Sheet1", [["Bob", 25], ["Carol", 28]])

    # Clear a range
    sheets.clear_values("SPREADSHEET_ID", "Sheet1!A1:D10")

    # Create a new spreadsheet
    result = sheets.create_spreadsheet("My New Sheet")
"""

import requests

from goliath import config

_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"


class SheetsClient:
    """Google Sheets API v4 client for reading and writing spreadsheet data."""

    def __init__(self):
        self._service_account_file = config.GOOGLE_SERVICE_ACCOUNT_FILE
        self._api_key = config.GOOGLE_SHEETS_API_KEY
        self._credentials = None
        self.session = requests.Session()

        if not self._service_account_file and not self._api_key:
            raise RuntimeError(
                "No Google Sheets credentials found. "
                "Set GOOGLE_SERVICE_ACCOUNT_FILE (read/write) or "
                "GOOGLE_SHEETS_API_KEY (read-only) in .env. "
                "See integrations/sheets.py for setup instructions."
            )

        if self._service_account_file:
            self._init_service_account()

    def _init_service_account(self):
        """Load service account credentials and set auth header."""
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self._credentials = service_account.Credentials.from_service_account_file(
            self._service_account_file, scopes=scopes,
        )
        self._refresh_token()

    def _refresh_token(self):
        """Refresh the access token if expired."""
        from google.auth.transport.requests import Request

        if self._credentials and (not self._credentials.valid or self._credentials.expired):
            self._credentials.refresh(Request())
            self.session.headers["Authorization"] = f"Bearer {self._credentials.token}"

    # -- public API --------------------------------------------------------

    def get_values(self, spreadsheet_id: str, range: str) -> list[list]:
        """Read values from a spreadsheet range.

        Args:
            spreadsheet_id: The ID of the spreadsheet (from the URL).
            range:          A1 notation range (e.g. "Sheet1!A1:D10").

        Returns:
            List of rows, each row a list of cell values.
        """
        data = self._get(f"/{spreadsheet_id}/values/{range}")
        return data.get("values", [])

    def update_values(
        self,
        spreadsheet_id: str,
        range: str,
        values: list[list],
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        """Write values to a spreadsheet range.

        Requires service account credentials.

        Args:
            spreadsheet_id:     The spreadsheet ID.
            range:              A1 notation range to write to.
            values:             2D list of values to write.
            value_input_option: How to interpret input ("RAW" or "USER_ENTERED").

        Returns:
            API response dict with updatedCells, updatedRows, etc.
        """
        self._require_service_account("update_values")
        return self._put(
            f"/{spreadsheet_id}/values/{range}",
            params={"valueInputOption": value_input_option},
            json={"range": range, "values": values},
        )

    def append_values(
        self,
        spreadsheet_id: str,
        range: str,
        values: list[list],
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        """Append rows after the last row with data in a range.

        Requires service account credentials.

        Args:
            spreadsheet_id:     The spreadsheet ID.
            range:              A1 notation range (e.g. "Sheet1").
            values:             2D list of rows to append.
            value_input_option: How to interpret input.

        Returns:
            API response dict.
        """
        self._require_service_account("append_values")
        return self._post(
            f"/{spreadsheet_id}/values/{range}:append",
            params={"valueInputOption": value_input_option},
            json={"range": range, "values": values},
        )

    def clear_values(self, spreadsheet_id: str, range: str) -> dict:
        """Clear all values in a range (formatting is preserved).

        Requires service account credentials.

        Args:
            spreadsheet_id: The spreadsheet ID.
            range:          A1 notation range to clear.

        Returns:
            API response dict.
        """
        self._require_service_account("clear_values")
        return self._post(f"/{spreadsheet_id}/values/{range}:clear", json={})

    def create_spreadsheet(self, title: str) -> dict:
        """Create a new spreadsheet.

        Requires service account credentials.

        Args:
            title: Title for the new spreadsheet.

        Returns:
            API response dict with spreadsheetId, spreadsheetUrl, etc.
        """
        self._require_service_account("create_spreadsheet")
        return self._post("", json={"properties": {"title": title}})

    # -- internal helpers --------------------------------------------------

    def _require_service_account(self, method: str):
        """Raise if service account is not configured (needed for writes)."""
        if not self._credentials:
            raise RuntimeError(
                f"{method}() requires a service account. "
                "Set GOOGLE_SERVICE_ACCOUNT_FILE in .env."
            )

    def _get(self, path: str, **kwargs) -> dict:
        if self._credentials:
            self._refresh_token()
        else:
            kwargs.setdefault("params", {})["key"] = self._api_key
        resp = self.session.get(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.post(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.put(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
