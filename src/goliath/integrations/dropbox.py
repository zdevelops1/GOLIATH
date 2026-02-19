"""
Dropbox Integration — upload, download, and manage files via the Dropbox API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.dropbox.com/developers/apps and click "Create app".

2. Choose:
   - Scoped access
   - Full Dropbox (or App folder for sandboxed access)
   - Give it a name (e.g. "GOLIATH")

3. Under the "Permissions" tab, enable:
   - files.metadata.read
   - files.metadata.write
   - files.content.read
   - files.content.write
   - sharing.read
   - sharing.write

4. Under the "Settings" tab, generate an access token.

5. Add to your .env:
     DROPBOX_ACCESS_TOKEN=sl.xxxxxxxxxxxxxxxx

   For long-lived access, use refresh tokens:
     DROPBOX_APP_KEY=xxxxxxxxxxxxxxxx
     DROPBOX_APP_SECRET=xxxxxxxxxxxxxxxx
     DROPBOX_REFRESH_TOKEN=xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Short-lived tokens expire after ~4 hours. Use refresh tokens for production.
- All paths must start with "/" (e.g. "/Documents/report.pdf").
- Max file upload via this client: 150 MB (uses single-call upload).
  For larger files, use upload sessions (not implemented here).
- Rate limit: ~600 requests/10 minutes per user.

Usage:
    from goliath.integrations.dropbox import DropboxClient

    dbx = DropboxClient()

    # List files in a folder
    files = dbx.list_folder("/Documents")

    # Upload a file
    dbx.upload("/local/report.pdf", "/Documents/report.pdf")

    # Download a file
    content = dbx.download("/Documents/report.pdf")

    # Create a shared link
    link = dbx.create_shared_link("/Documents/report.pdf")

    # Search for files
    results = dbx.search("quarterly report")
"""

import requests

from goliath import config

_API_BASE = "https://api.dropboxapi.com/2"
_CONTENT_BASE = "https://content.dropboxapi.com/2"


class DropboxClient:
    """Dropbox API client for file management."""

    def __init__(self):
        if not config.DROPBOX_ACCESS_TOKEN:
            raise RuntimeError(
                "DROPBOX_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/dropbox.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.DROPBOX_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- File operations ---------------------------------------------------

    def list_folder(self, path: str = "", recursive: bool = False) -> list[dict]:
        """List files and folders at the given path.

        Args:
            path:      Dropbox path (e.g. "/Documents"). Empty string for root.
            recursive: If True, list all descendants recursively.

        Returns:
            List of file/folder metadata dicts.
        """
        data = {"path": path, "recursive": recursive, "limit": 2000}
        resp = self._post("/files/list_folder", json=data)
        entries = resp.get("entries", [])

        # Handle pagination
        while resp.get("has_more"):
            resp = self._post(
                "/files/list_folder/continue",
                json={"cursor": resp["cursor"]},
            )
            entries.extend(resp.get("entries", []))

        return entries

    def get_metadata(self, path: str) -> dict:
        """Get metadata for a file or folder.

        Args:
            path: Dropbox path (e.g. "/Documents/report.pdf").

        Returns:
            Metadata dict with name, size, modified date, etc.
        """
        return self._post("/files/get_metadata", json={"path": path})

    def upload(
        self, local_path: str, dropbox_path: str, overwrite: bool = False
    ) -> dict:
        """Upload a file to Dropbox.

        Args:
            local_path:    Local file path to upload.
            dropbox_path:  Destination path in Dropbox.
            overwrite:     If True, overwrite existing file.

        Returns:
            Uploaded file metadata dict.
        """
        import json

        mode = "overwrite" if overwrite else "add"
        args = {
            "path": dropbox_path,
            "mode": mode,
            "autorename": not overwrite,
        }

        with open(local_path, "rb") as f:
            resp = requests.post(
                f"{_CONTENT_BASE}/files/upload",
                headers={
                    "Authorization": f"Bearer {config.DROPBOX_ACCESS_TOKEN}",
                    "Content-Type": "application/octet-stream",
                    "Dropbox-API-Arg": json.dumps(args),
                },
                data=f,
            )
        resp.raise_for_status()
        return resp.json()

    def download(self, path: str) -> bytes:
        """Download a file from Dropbox.

        Args:
            path: Dropbox path (e.g. "/Documents/report.pdf").

        Returns:
            File content as bytes.
        """
        import json

        resp = requests.post(
            f"{_CONTENT_BASE}/files/download",
            headers={
                "Authorization": f"Bearer {config.DROPBOX_ACCESS_TOKEN}",
                "Content-Type": "",
                "Dropbox-API-Arg": json.dumps({"path": path}),
            },
        )
        resp.raise_for_status()
        return resp.content

    def delete(self, path: str) -> dict:
        """Delete a file or folder.

        Args:
            path: Dropbox path to delete.

        Returns:
            Deleted item metadata dict.
        """
        return self._post("/files/delete_v2", json={"path": path})

    def move(self, from_path: str, to_path: str) -> dict:
        """Move a file or folder.

        Args:
            from_path: Current Dropbox path.
            to_path:   New Dropbox path.

        Returns:
            Moved item metadata dict.
        """
        return self._post(
            "/files/move_v2",
            json={"from_path": from_path, "to_path": to_path},
        )

    def copy(self, from_path: str, to_path: str) -> dict:
        """Copy a file or folder.

        Args:
            from_path: Source Dropbox path.
            to_path:   Destination Dropbox path.

        Returns:
            Copied item metadata dict.
        """
        return self._post(
            "/files/copy_v2",
            json={"from_path": from_path, "to_path": to_path},
        )

    def create_folder(self, path: str) -> dict:
        """Create a folder.

        Args:
            path: Dropbox path for the new folder.

        Returns:
            Folder metadata dict.
        """
        return self._post("/files/create_folder_v2", json={"path": path})

    # -- Sharing -----------------------------------------------------------

    def create_shared_link(self, path: str) -> str:
        """Create a shared link for a file or folder.

        Args:
            path: Dropbox path.

        Returns:
            Public URL string.
        """
        resp = self._post(
            "/sharing/create_shared_link_with_settings",
            json={"path": path},
        )
        return resp.get("url", "")

    # -- Search ------------------------------------------------------------

    def search(self, query: str, path: str = "", max_results: int = 20) -> list[dict]:
        """Search for files and folders.

        Args:
            query:       Search query string.
            path:        Scope search to this path (empty for all).
            max_results: Maximum number of results.

        Returns:
            List of match metadata dicts.
        """
        data = {"query": query, "options": {"max_results": max_results}}
        if path:
            data["options"]["path"] = path
        resp = self._post("/files/search_v2", json=data)
        return [
            m.get("metadata", {}).get("metadata", {}) for m in resp.get("matches", [])
        ]

    # -- internal helpers --------------------------------------------------

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
