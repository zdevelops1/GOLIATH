"""
Firebase Integration — manage Firestore, Realtime Database, and Auth via the Firebase REST APIs.

SETUP INSTRUCTIONS
==================

1. Go to the Firebase console at https://console.firebase.google.com/

2. Select your project (or create one).

3. For REST API access you need:
   - **Project ID**: Found on the project settings page.
   - **Web API Key**: Found under Project Settings > General.
   - **Service Account Key** (optional, for admin access):
     Go to Project Settings > Service accounts > Generate new private key.

4. Add to your .env:
     FIREBASE_PROJECT_ID=your-project-id
     FIREBASE_API_KEY=AIzaSyB...
     FIREBASE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json  (optional)
     FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com  (for RTDB)

IMPORTANT NOTES
===============
- This client uses the Firestore REST API and Firebase Auth REST API.
- For full admin access (bypassing security rules), use a service account.
- Firestore API docs: https://firebase.google.com/docs/firestore/reference/rest
- Auth API docs: https://firebase.google.com/docs/reference/rest/auth
- Realtime Database docs: https://firebase.google.com/docs/database/rest/start
- Rate limits vary by service and plan.

Usage:
    from goliath.integrations.firebase import FirebaseClient

    fb = FirebaseClient()

    # -- Firestore --

    # Create/set a document
    fb.set_document("users", "user123", {"name": "Jane", "email": "jane@example.com"})

    # Get a document
    doc = fb.get_document("users", "user123")

    # Query a collection
    docs = fb.list_documents("users", page_size=10)

    # Delete a document
    fb.delete_document("users", "user123")

    # -- Realtime Database --

    # Set data
    fb.rtdb_set("/messages/msg1", {"text": "Hello!", "sender": "user123"})

    # Get data
    data = fb.rtdb_get("/messages/msg1")

    # Push data (auto-generated key)
    ref = fb.rtdb_push("/messages", {"text": "New message", "sender": "user456"})

    # -- Auth --

    # Sign up a new user
    user = fb.auth_sign_up(email="new@example.com", password="secret123")

    # Sign in
    user = fb.auth_sign_in(email="new@example.com", password="secret123")
"""

import json as _json

import requests

from goliath import config

_FIRESTORE_BASE = "https://firestore.googleapis.com/v1"
_AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"


class FirebaseClient:
    """Firebase REST API client for Firestore, Realtime Database, and Auth."""

    def __init__(self):
        if not config.FIREBASE_PROJECT_ID:
            raise RuntimeError(
                "FIREBASE_PROJECT_ID is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/firebase.py for setup instructions."
            )

        self.project_id = config.FIREBASE_PROJECT_ID
        self.api_key = config.FIREBASE_API_KEY
        self.database_url = config.FIREBASE_DATABASE_URL
        self._firestore_base = (
            f"{_FIRESTORE_BASE}/projects/{self.project_id}/databases/(default)/documents"
        )

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # If a service account file is provided, get an access token
        self._access_token: str | None = None
        if config.FIREBASE_SERVICE_ACCOUNT_FILE:
            self._load_service_account(config.FIREBASE_SERVICE_ACCOUNT_FILE)

    # -- Firestore ---------------------------------------------------------

    def set_document(
        self, collection: str, document_id: str, fields: dict
    ) -> dict:
        """Create or overwrite a Firestore document.

        Args:
            collection:  Collection name.
            document_id: Document ID.
            fields:      Document fields as a plain dict (auto-converted to Firestore format).

        Returns:
            Firestore document dict.
        """
        url = f"{self._firestore_base}/{collection}/{document_id}"
        body = {"fields": self._encode_fields(fields)}
        resp = self._request("PATCH", url, json=body)
        return self._decode_document(resp)

    def get_document(self, collection: str, document_id: str) -> dict:
        """Get a Firestore document.

        Args:
            collection:  Collection name.
            document_id: Document ID.

        Returns:
            Decoded document dict with fields.
        """
        url = f"{self._firestore_base}/{collection}/{document_id}"
        resp = self._request("GET", url)
        return self._decode_document(resp)

    def delete_document(self, collection: str, document_id: str) -> None:
        """Delete a Firestore document.

        Args:
            collection:  Collection name.
            document_id: Document ID.
        """
        url = f"{self._firestore_base}/{collection}/{document_id}"
        self._request("DELETE", url)

    def list_documents(
        self, collection: str, page_size: int = 20, page_token: str | None = None
    ) -> list[dict]:
        """List documents in a Firestore collection.

        Args:
            collection: Collection name.
            page_size:  Max results per page.
            page_token: Pagination token from a previous response.

        Returns:
            List of decoded document dicts.
        """
        url = f"{self._firestore_base}/{collection}"
        params: dict = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        resp = self._request("GET", url, params=params)
        return [self._decode_document(doc) for doc in resp.get("documents", [])]

    # -- Realtime Database -------------------------------------------------

    def rtdb_get(self, path: str) -> dict | list | str | None:
        """Get data from the Realtime Database.

        Args:
            path: Database path (e.g. "/messages/msg1").

        Returns:
            Data at the path.
        """
        url = self._rtdb_url(path)
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def rtdb_set(self, path: str, data: dict) -> dict:
        """Set (overwrite) data at a Realtime Database path.

        Args:
            path: Database path.
            data: Data to write.

        Returns:
            Written data.
        """
        url = self._rtdb_url(path)
        resp = self.session.put(url, json=data)
        resp.raise_for_status()
        return resp.json()

    def rtdb_update(self, path: str, data: dict) -> dict:
        """Update (merge) data at a Realtime Database path.

        Args:
            path: Database path.
            data: Fields to merge.

        Returns:
            Merged data.
        """
        url = self._rtdb_url(path)
        resp = self.session.patch(url, json=data)
        resp.raise_for_status()
        return resp.json()

    def rtdb_push(self, path: str, data: dict) -> dict:
        """Push data with an auto-generated key.

        Args:
            path: Database path.
            data: Data to push.

        Returns:
            Dict with "name" (the generated key).
        """
        url = self._rtdb_url(path)
        resp = self.session.post(url, json=data)
        resp.raise_for_status()
        return resp.json()

    def rtdb_delete(self, path: str) -> None:
        """Delete data at a Realtime Database path.

        Args:
            path: Database path.
        """
        url = self._rtdb_url(path)
        resp = self.session.delete(url)
        resp.raise_for_status()

    # -- Auth --------------------------------------------------------------

    def auth_sign_up(self, email: str, password: str) -> dict:
        """Create a new user with email and password.

        Args:
            email:    User email.
            password: User password.

        Returns:
            Auth response with idToken, refreshToken, localId, etc.
        """
        return self._auth_request("signUp", email=email, password=password)

    def auth_sign_in(self, email: str, password: str) -> dict:
        """Sign in a user with email and password.

        Args:
            email:    User email.
            password: User password.

        Returns:
            Auth response with idToken, refreshToken, localId, etc.
        """
        return self._auth_request(
            "signInWithPassword", email=email, password=password
        )

    def auth_get_user(self, id_token: str) -> dict:
        """Get user data using an ID token.

        Args:
            id_token: Firebase ID token from sign-in.

        Returns:
            User data dict.
        """
        resp = self.session.post(
            f"{_AUTH_BASE}/accounts:lookup",
            params={"key": self.api_key},
            json={"idToken": id_token},
        )
        resp.raise_for_status()
        users = resp.json().get("users", [])
        return users[0] if users else {}

    # -- internal helpers --------------------------------------------------

    def _load_service_account(self, path: str) -> None:
        """Load service account credentials and get an access token via Google OAuth2."""
        try:
            from google.oauth2 import service_account as sa
            from google.auth.transport.requests import Request

            creds = sa.Credentials.from_service_account_file(
                path,
                scopes=[
                    "https://www.googleapis.com/auth/datastore",
                    "https://www.googleapis.com/auth/firebase",
                ],
            )
            creds.refresh(Request())
            self._access_token = creds.token
        except ImportError:
            raise RuntimeError(
                "google-auth package is required for service account auth. "
                "Install it with: pip install google-auth"
            )

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Make an authenticated request."""
        headers = kwargs.pop("headers", {})
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        resp = self.session.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def _rtdb_url(self, path: str) -> str:
        """Build a Realtime Database URL."""
        if not self.database_url:
            raise RuntimeError(
                "FIREBASE_DATABASE_URL is not set. Required for Realtime Database access."
            )
        path = path.strip("/")
        base = self.database_url.rstrip("/")
        auth_param = f"?auth={self._access_token}" if self._access_token else ""
        return f"{base}/{path}.json{auth_param}"

    def _auth_request(self, action: str, **kwargs) -> dict:
        """Make a Firebase Auth REST API request."""
        if not self.api_key:
            raise RuntimeError(
                "FIREBASE_API_KEY is required for Auth operations."
            )
        payload = {"returnSecureToken": True, **kwargs}
        resp = self.session.post(
            f"{_AUTH_BASE}/accounts:{action}",
            params={"key": self.api_key},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _encode_fields(data: dict) -> dict:
        """Convert a plain dict to Firestore Value format."""
        encoded = {}
        for key, value in data.items():
            if isinstance(value, str):
                encoded[key] = {"stringValue": value}
            elif isinstance(value, bool):
                encoded[key] = {"booleanValue": value}
            elif isinstance(value, int):
                encoded[key] = {"integerValue": str(value)}
            elif isinstance(value, float):
                encoded[key] = {"doubleValue": value}
            elif value is None:
                encoded[key] = {"nullValue": None}
            elif isinstance(value, list):
                encoded[key] = {
                    "arrayValue": {
                        "values": [
                            FirebaseClient._encode_value(v) for v in value
                        ]
                    }
                }
            elif isinstance(value, dict):
                encoded[key] = {
                    "mapValue": {"fields": FirebaseClient._encode_fields(value)}
                }
            else:
                encoded[key] = {"stringValue": str(value)}
        return encoded

    @staticmethod
    def _encode_value(value) -> dict:
        """Encode a single value to Firestore format."""
        if isinstance(value, str):
            return {"stringValue": value}
        if isinstance(value, bool):
            return {"booleanValue": value}
        if isinstance(value, int):
            return {"integerValue": str(value)}
        if isinstance(value, float):
            return {"doubleValue": value}
        if value is None:
            return {"nullValue": None}
        return {"stringValue": str(value)}

    @staticmethod
    def _decode_document(doc: dict) -> dict:
        """Decode a Firestore document to a plain dict."""
        if not doc or "fields" not in doc:
            return doc
        result = {"_id": doc.get("name", "").split("/")[-1]}
        for key, value in doc.get("fields", {}).items():
            result[key] = FirebaseClient._decode_value(value)
        return result

    @staticmethod
    def _decode_value(value: dict):
        """Decode a single Firestore value."""
        if "stringValue" in value:
            return value["stringValue"]
        if "integerValue" in value:
            return int(value["integerValue"])
        if "doubleValue" in value:
            return value["doubleValue"]
        if "booleanValue" in value:
            return value["booleanValue"]
        if "nullValue" in value:
            return None
        if "arrayValue" in value:
            return [
                FirebaseClient._decode_value(v)
                for v in value["arrayValue"].get("values", [])
            ]
        if "mapValue" in value:
            return {
                k: FirebaseClient._decode_value(v)
                for k, v in value["mapValue"].get("fields", {}).items()
            }
        return value
