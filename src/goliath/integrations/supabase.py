"""
Supabase Integration — manage database rows, storage, and auth via the Supabase REST APIs.

SETUP INSTRUCTIONS
==================

1. Go to https://supabase.com/ and log in (or create a project).

2. In your project dashboard, go to Settings > API.

3. Copy:
   - **Project URL**: https://<project-ref>.supabase.co
   - **anon (public) key**: for client-side / public access
   - **service_role key**: for full admin access (bypasses RLS)

4. Add to your .env:
     SUPABASE_URL=https://your-project-ref.supabase.co
     SUPABASE_KEY=your-anon-or-service-role-key

   Use the service_role key for server-side automation (full access).
   Use the anon key if you want to respect Row Level Security policies.

IMPORTANT NOTES
===============
- Supabase exposes a PostgREST API for database operations.
- Auth uses the GoTrue API bundled with Supabase.
- Storage uses the Supabase Storage API.
- API docs: https://supabase.com/docs/guides/api
- Rate limits depend on your plan.

Usage:
    from goliath.integrations.supabase import SupabaseClient

    sb = SupabaseClient()

    # -- Database (PostgREST) --

    # Select rows
    rows = sb.select("users", columns="id,name,email", limit=10)

    # Select with filter
    rows = sb.select("users", columns="*", filters={"email": "eq.jane@example.com"})

    # Insert a row
    sb.insert("users", {"name": "Jane", "email": "jane@example.com"})

    # Update rows
    sb.update("users", {"name": "Jane Doe"}, filters={"id": "eq.1"})

    # Delete rows
    sb.delete("users", filters={"id": "eq.1"})

    # Call an RPC (database function)
    result = sb.rpc("my_function", {"param1": "value1"})

    # -- Storage --

    # List buckets
    buckets = sb.list_buckets()

    # Upload a file
    sb.upload_file("avatars", "user1.png", file_path="/path/to/image.png")

    # Get a public URL
    url = sb.get_public_url("avatars", "user1.png")

    # -- Auth --

    # Sign up
    user = sb.auth_sign_up(email="new@example.com", password="secret123")

    # Sign in
    session = sb.auth_sign_in(email="new@example.com", password="secret123")
"""

from pathlib import Path

import requests

from goliath import config


class SupabaseClient:
    """Supabase client for database, storage, and auth operations."""

    def __init__(self):
        if not config.SUPABASE_URL:
            raise RuntimeError(
                "SUPABASE_URL is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/supabase.py for setup instructions."
            )
        if not config.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_KEY is not set. "
                "Add it to .env (anon key or service_role key)."
            )

        self._url = config.SUPABASE_URL.rstrip("/")
        self._rest = f"{self._url}/rest/v1"
        self._auth = f"{self._url}/auth/v1"
        self._storage = f"{self._url}/storage/v1"

        self.session = requests.Session()
        self.session.headers.update({
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        })

    # -- Database (PostgREST) ----------------------------------------------

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict | None = None,
        order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """Select rows from a table.

        Args:
            table:   Table name.
            columns: Comma-separated columns (or "*").
            filters: Dict of column filters (e.g. {"age": "gt.18", "name": "eq.Jane"}).
            order:   Order clause (e.g. "created_at.desc").
            limit:   Max rows.
            offset:  Row offset.

        Returns:
            List of row dicts.
        """
        params: dict = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        resp = self.session.get(f"{self._rest}/{table}", params=params)
        resp.raise_for_status()
        return resp.json()

    def insert(self, table: str, data: dict | list[dict]) -> list[dict]:
        """Insert one or more rows.

        Args:
            table: Table name.
            data:  Row dict or list of row dicts.

        Returns:
            List of inserted rows.
        """
        resp = self.session.post(f"{self._rest}/{table}", json=data)
        resp.raise_for_status()
        return resp.json()

    def update(self, table: str, data: dict, filters: dict) -> list[dict]:
        """Update rows matching filters.

        Args:
            table:   Table name.
            data:    Fields to update.
            filters: PostgREST filters (e.g. {"id": "eq.1"}).

        Returns:
            List of updated rows.
        """
        resp = self.session.patch(
            f"{self._rest}/{table}", json=data, params=filters
        )
        resp.raise_for_status()
        return resp.json()

    def upsert(self, table: str, data: dict | list[dict]) -> list[dict]:
        """Upsert (insert or update) rows.

        Args:
            table: Table name.
            data:  Row dict or list of row dicts.

        Returns:
            List of upserted rows.
        """
        headers = {"Prefer": "resolution=merge-duplicates,return=representation"}
        resp = self.session.post(
            f"{self._rest}/{table}", json=data, headers=headers
        )
        resp.raise_for_status()
        return resp.json()

    def delete(self, table: str, filters: dict) -> list[dict]:
        """Delete rows matching filters.

        Args:
            table:   Table name.
            filters: PostgREST filters (e.g. {"id": "eq.1"}).

        Returns:
            List of deleted rows.
        """
        resp = self.session.delete(f"{self._rest}/{table}", params=filters)
        resp.raise_for_status()
        return resp.json()

    def rpc(self, function_name: str, params: dict | None = None) -> dict | list:
        """Call a database function (RPC).

        Args:
            function_name: Postgres function name.
            params:        Function parameters.

        Returns:
            Function result.
        """
        resp = self.session.post(
            f"{self._rest}/rpc/{function_name}", json=params or {}
        )
        resp.raise_for_status()
        return resp.json()

    # -- Storage -----------------------------------------------------------

    def list_buckets(self) -> list[dict]:
        """List storage buckets.

        Returns:
            List of bucket dicts.
        """
        resp = self.session.get(f"{self._storage}/bucket")
        resp.raise_for_status()
        return resp.json()

    def list_files(self, bucket: str, path: str = "", limit: int = 100) -> list[dict]:
        """List files in a bucket.

        Args:
            bucket: Bucket name.
            path:   Folder path within the bucket.
            limit:  Max files.

        Returns:
            List of file/folder dicts.
        """
        resp = self.session.post(
            f"{self._storage}/object/list/{bucket}",
            json={"prefix": path, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    def upload_file(
        self,
        bucket: str,
        object_path: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload a file to storage.

        Args:
            bucket:       Bucket name.
            object_path:  Destination path in the bucket.
            file_path:    Local file path to upload.
            content_type: MIME type.

        Returns:
            Upload result dict.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            resp = self.session.post(
                f"{self._storage}/object/{bucket}/{object_path}",
                data=f.read(),
                headers={
                    "Content-Type": content_type,
                    "apikey": self.session.headers["apikey"],
                    "Authorization": self.session.headers["Authorization"],
                },
            )
        resp.raise_for_status()
        return resp.json()

    def delete_file(self, bucket: str, paths: list[str]) -> list[dict]:
        """Delete files from storage.

        Args:
            bucket: Bucket name.
            paths:  List of object paths to delete.

        Returns:
            List of deleted file dicts.
        """
        resp = self.session.delete(
            f"{self._storage}/object/{bucket}", json={"prefixes": paths}
        )
        resp.raise_for_status()
        return resp.json()

    def get_public_url(self, bucket: str, object_path: str) -> str:
        """Get the public URL for a file.

        Args:
            bucket:      Bucket name.
            object_path: Object path in the bucket.

        Returns:
            Public URL string.
        """
        return f"{self._storage}/object/public/{bucket}/{object_path}"

    # -- Auth --------------------------------------------------------------

    def auth_sign_up(self, email: str, password: str) -> dict:
        """Sign up a new user with email and password.

        Args:
            email:    User email.
            password: User password.

        Returns:
            Auth response with user, session, access_token, etc.
        """
        resp = self.session.post(
            f"{self._auth}/signup",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        return resp.json()

    def auth_sign_in(self, email: str, password: str) -> dict:
        """Sign in a user with email and password.

        Args:
            email:    User email.
            password: User password.

        Returns:
            Auth response with access_token, refresh_token, user, etc.
        """
        resp = self.session.post(
            f"{self._auth}/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        return resp.json()

    def auth_get_user(self, access_token: str) -> dict:
        """Get user details from an access token.

        Args:
            access_token: JWT access token from sign-in.

        Returns:
            User dict.
        """
        resp = self.session.get(
            f"{self._auth}/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
