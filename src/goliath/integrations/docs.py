"""
Google Docs Integration — read, create, and update documents.

SETUP INSTRUCTIONS
==================

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create a service account (or reuse the one from Sheets/Drive/Calendar).
3. Download its JSON key file.
4. Enable the Google Docs API for your project:
     https://console.cloud.google.com/apis/library/docs.googleapis.com
5. Share existing documents with the service account email
   (name@project-id.iam.gserviceaccount.com) for access.
6. Add the path to your .env:
     GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

Usage:
    from goliath.integrations.docs import DocsClient

    docs = DocsClient()

    # Get a document's content
    doc = docs.get_document("DOCUMENT_ID")

    # Create a new document
    result = docs.create_document("Meeting Notes")

    # Append text to the end of a document
    docs.append_text("DOCUMENT_ID", "\\nAction items from today's meeting:\\n- Item 1\\n- Item 2")

    # Batch update (advanced — raw API requests)
    docs.batch_update("DOCUMENT_ID", requests=[
        {"insertText": {"location": {"index": 1}, "text": "Hello World\\n"}}
    ])
"""

import requests

from goliath import config

_DOCS_BASE = "https://docs.googleapis.com/v1/documents"


class DocsClient:
    """Google Docs API v1 client for reading and writing documents."""

    def __init__(self):
        if not config.GOOGLE_SERVICE_ACCOUNT_FILE:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_FILE is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/docs.py for setup instructions."
            )

        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        scopes = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive",
        ]
        self._credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes,
        )
        self.session = requests.Session()
        self._refresh_token()

    def _refresh_token(self):
        """Refresh the access token if expired."""
        from google.auth.transport.requests import Request

        if not self._credentials.valid or self._credentials.expired:
            self._credentials.refresh(Request())
            self.session.headers["Authorization"] = f"Bearer {self._credentials.token}"

    # -- public API --------------------------------------------------------

    def get_document(self, document_id: str) -> dict:
        """Get the full document resource including body content.

        Args:
            document_id: The Google Docs document ID (from the URL).

        Returns:
            Document resource dict with title, body, etc.
        """
        return self._get(f"/{document_id}")

    def create_document(self, title: str) -> dict:
        """Create a new empty document.

        Args:
            title: Title for the new document.

        Returns:
            Created document resource dict with documentId, title, etc.
        """
        return self._post("", json={"title": title})

    def append_text(self, document_id: str, text: str) -> dict:
        """Append text to the end of a document.

        Args:
            document_id: The document ID.
            text:        Text to append.

        Returns:
            BatchUpdate response dict.
        """
        # Get the document to find the end index
        doc = self.get_document(document_id)
        body = doc.get("body", {})
        content = body.get("content", [])

        # The endIndex of the last content element is where we insert
        end_index = 1
        if content:
            end_index = content[-1].get("endIndex", 1) - 1
            if end_index < 1:
                end_index = 1

        return self.batch_update(document_id, requests=[
            {"insertText": {"location": {"index": end_index}, "text": text}},
        ])

    def batch_update(self, document_id: str, requests: list[dict]) -> dict:
        """Send a batch update to a document.

        This is the low-level API for all document mutations. Each request
        in the list is a Docs API request object (insertText, deleteContent,
        updateTextStyle, etc.).

        See: https://developers.google.com/docs/api/reference/rest/v1/documents/batchUpdate

        Args:
            document_id: The document ID.
            requests:    List of update request dicts.

        Returns:
            BatchUpdate response dict.
        """
        return self._post(
            f"/{document_id}:batchUpdate",
            json={"requests": requests},
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.get(f"{_DOCS_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.post(f"{_DOCS_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
