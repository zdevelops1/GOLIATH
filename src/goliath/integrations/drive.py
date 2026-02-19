"""
Google Drive Integration — list, upload, download, and manage files.

SETUP INSTRUCTIONS
==================

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create a service account (or reuse the one from Sheets/Calendar/Docs).
3. Download its JSON key file.
4. Enable the Google Drive API for your project:
     https://console.cloud.google.com/apis/library/drive.googleapis.com
5. To access existing files, share them with the service account email
   (name@project-id.iam.gserviceaccount.com).
6. Add the path to your .env:
     GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

Usage:
    from goliath.integrations.drive import DriveClient

    drive = DriveClient()

    # List files
    files = drive.list_files(query="mimeType='application/pdf'")

    # Upload a file
    result = drive.upload_file("report.pdf", folder_id="FOLDER_ID")

    # Download a file
    drive.download_file("FILE_ID", "local_copy.pdf")

    # Create a folder
    folder = drive.create_folder("Project Assets")

    # Share a file
    drive.share_file("FILE_ID", email="user@example.com", role="reader")

    # Delete a file
    drive.delete_file("FILE_ID")
"""

from pathlib import Path

import requests

from goliath import config

_BASE_URL = "https://www.googleapis.com/drive/v3"
_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"


class DriveClient:
    """Google Drive API v3 client for file management."""

    def __init__(self):
        if not config.GOOGLE_SERVICE_ACCOUNT_FILE:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_FILE is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/drive.py for setup instructions."
            )

        from google.oauth2 import service_account

        scopes = ["https://www.googleapis.com/auth/drive"]
        self._credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=scopes,
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

    def list_files(
        self,
        query: str | None = None,
        page_size: int = 100,
        order_by: str = "modifiedTime desc",
        fields: str = "files(id,name,mimeType,size,modifiedTime,parents)",
    ) -> list[dict]:
        """List files in Drive.

        Args:
            query:     Drive search query (e.g. "mimeType='application/pdf'").
                       See https://developers.google.com/drive/api/guides/search-files
            page_size: Max results per page (1–1000).
            order_by:  Sort order.
            fields:    Fields to include in the response.

        Returns:
            List of file metadata dicts.
        """
        params: dict = {
            "pageSize": page_size,
            "orderBy": order_by,
            "fields": f"nextPageToken,{fields}",
        }
        if query:
            params["q"] = query
        return self._get("/files", params=params).get("files", [])

    def get_file(self, file_id: str) -> dict:
        """Get metadata for a single file.

        Args:
            file_id: The Drive file ID.

        Returns:
            File metadata dict.
        """
        return self._get(
            f"/files/{file_id}",
            params={"fields": "id,name,mimeType,size,modifiedTime,parents,webViewLink"},
        )

    def upload_file(
        self,
        file_path: str,
        name: str | None = None,
        folder_id: str | None = None,
        mime_type: str | None = None,
    ) -> dict:
        """Upload a file to Drive.

        Args:
            file_path: Local path to the file.
            name:      Name for the file in Drive (defaults to local filename).
            folder_id: Optional parent folder ID.
            mime_type: Optional MIME type override.

        Returns:
            Uploaded file metadata dict.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        metadata: dict = {"name": name or path.name}
        if folder_id:
            metadata["parents"] = [folder_id]

        self._refresh_token()

        # Multipart upload: metadata + file content
        import json

        with open(path, "rb") as f:
            resp = self.session.post(
                _UPLOAD_URL,
                params={
                    "uploadType": "multipart",
                    "fields": "id,name,mimeType,size,webViewLink",
                },
                files={
                    "metadata": (
                        "metadata.json",
                        json.dumps(metadata),
                        "application/json",
                    ),
                    "file": (path.name, f, mime_type or "application/octet-stream"),
                },
            )
        resp.raise_for_status()
        return resp.json()

    def download_file(self, file_id: str, destination: str) -> str:
        """Download a file from Drive to a local path.

        Args:
            file_id:     The Drive file ID.
            destination: Local file path to save to.

        Returns:
            The absolute path to the downloaded file.
        """
        self._refresh_token()
        resp = self.session.get(
            f"{_BASE_URL}/files/{file_id}",
            params={"alt": "media"},
            stream=True,
        )
        resp.raise_for_status()

        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return str(dest.resolve())

    def create_folder(self, name: str, parent_id: str | None = None) -> dict:
        """Create a folder in Drive.

        Args:
            name:      Folder name.
            parent_id: Optional parent folder ID.

        Returns:
            Created folder metadata dict.
        """
        metadata: dict = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        return self._post(
            "/files",
            params={"fields": "id,name,mimeType,webViewLink"},
            json=metadata,
        )

    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file or folder.

        Args:
            file_id: The Drive file/folder ID.
        """
        self._delete(f"/files/{file_id}")

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
        send_notification: bool = True,
    ) -> dict:
        """Share a file with a user.

        Args:
            file_id:            The Drive file ID.
            email:              Email address of the user to share with.
            role:               Permission role ("reader", "writer", "commenter").
            send_notification:  Whether to send an email notification.

        Returns:
            Permission metadata dict.
        """
        return self._post(
            f"/files/{file_id}/permissions",
            params={"sendNotificationEmail": str(send_notification).lower()},
            json={"type": "user", "role": role, "emailAddress": email},
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.get(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        self._refresh_token()
        resp = self.session.post(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, **kwargs) -> None:
        self._refresh_token()
        resp = self.session.delete(f"{_BASE_URL}{path}", **kwargs)
        resp.raise_for_status()
