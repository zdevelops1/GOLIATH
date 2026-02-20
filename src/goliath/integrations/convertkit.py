"""
ConvertKit Integration — manage subscribers, forms, sequences, and broadcasts via the ConvertKit API.

SETUP INSTRUCTIONS
==================

1. Log in to ConvertKit at https://app.convertkit.com/

2. Go to Settings > Advanced > API
   (https://app.convertkit.com/account_settings/advanced_settings).

3. Copy your API Key and API Secret.

4. Add to your .env:
     CONVERTKIT_API_KEY=your_api_key
     CONVERTKIT_API_SECRET=your_api_secret

IMPORTANT NOTES
===============
- Some endpoints use api_key (public), others use api_secret (private).
- API docs: https://developers.convertkit.com/
- Rate limit: 120 requests per minute.
- Subscriber management requires api_secret; form listing uses api_key.

Usage:
    from goliath.integrations.convertkit import ConvertKitClient

    ck = ConvertKitClient()

    # List subscribers
    subs = ck.list_subscribers()

    # Get a subscriber
    sub = ck.get_subscriber(subscriber_id=12345)

    # Add a subscriber to a form
    ck.add_subscriber_to_form(form_id=67890, email="reader@example.com")

    # Tag a subscriber
    ck.tag_subscriber(tag_id=111, email="reader@example.com")

    # List forms
    forms = ck.list_forms()

    # List sequences (automations)
    sequences = ck.list_sequences()

    # Create a broadcast (email)
    broadcast = ck.create_broadcast(
        subject="Weekly Update",
        content="<p>Here is your weekly update.</p>",
    )

    # List tags
    tags = ck.list_tags()
"""

import requests

from goliath import config

_API_BASE = "https://api.convertkit.com/v3"


class ConvertKitClient:
    """ConvertKit API client for subscribers, forms, sequences, and broadcasts."""

    def __init__(self):
        if not config.CONVERTKIT_API_SECRET:
            raise RuntimeError(
                "CONVERTKIT_API_SECRET is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/convertkit.py for setup instructions."
            )

        self.api_key = config.CONVERTKIT_API_KEY
        self.api_secret = config.CONVERTKIT_API_SECRET
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Subscribers -------------------------------------------------------

    def list_subscribers(
        self, page: int = 1, sort_order: str = "desc"
    ) -> list[dict]:
        """List subscribers.

        Args:
            page:       Page number.
            sort_order: "asc" or "desc".

        Returns:
            List of subscriber dicts.
        """
        params = {
            "api_secret": self.api_secret,
            "page": page,
            "sort_order": sort_order,
        }
        return self._get("/subscribers", params=params).get("subscribers", [])

    def get_subscriber(self, subscriber_id: int) -> dict:
        """Get a subscriber by ID.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            Subscriber dict.
        """
        params = {"api_secret": self.api_secret}
        return self._get(f"/subscribers/{subscriber_id}", params=params).get(
            "subscriber", {}
        )

    def add_subscriber_to_form(
        self,
        form_id: int,
        email: str,
        first_name: str | None = None,
        **kwargs,
    ) -> dict:
        """Subscribe an email to a form.

        Args:
            form_id:    Form ID.
            email:      Subscriber email.
            first_name: Optional first name.
            kwargs:     Additional fields (fields, tags, etc.).

        Returns:
            Subscription dict.
        """
        data: dict = {"api_key": self.api_key, "email": email, **kwargs}
        if first_name:
            data["first_name"] = first_name
        return self._post(f"/forms/{form_id}/subscribe", json=data).get(
            "subscription", {}
        )

    def unsubscribe(self, email: str) -> dict:
        """Unsubscribe an email.

        Args:
            email: Subscriber email.

        Returns:
            Subscriber dict.
        """
        return self._put(
            "/unsubscribe", json={"api_secret": self.api_secret, "email": email}
        ).get("subscriber", {})

    # -- Tags --------------------------------------------------------------

    def list_tags(self) -> list[dict]:
        """List all tags.

        Returns:
            List of tag dicts with id and name.
        """
        return self._get("/tags", params={"api_key": self.api_key}).get("tags", [])

    def tag_subscriber(self, tag_id: int, email: str, **kwargs) -> dict:
        """Tag a subscriber.

        Args:
            tag_id: Tag ID.
            email:  Subscriber email.
            kwargs: Additional fields (first_name, fields, etc.).

        Returns:
            Subscription dict.
        """
        data: dict = {"api_secret": self.api_secret, "email": email, **kwargs}
        return self._post(f"/tags/{tag_id}/subscribe", json=data).get(
            "subscription", {}
        )

    def remove_tag(self, tag_id: int, subscriber_id: int) -> None:
        """Remove a tag from a subscriber.

        Args:
            tag_id:        Tag ID.
            subscriber_id: Subscriber ID.
        """
        resp = self.session.delete(
            f"{_API_BASE}/subscribers/{subscriber_id}/tags/{tag_id}",
            params={"api_secret": self.api_secret},
        )
        resp.raise_for_status()

    # -- Forms -------------------------------------------------------------

    def list_forms(self) -> list[dict]:
        """List all forms.

        Returns:
            List of form dicts.
        """
        return self._get("/forms", params={"api_key": self.api_key}).get("forms", [])

    # -- Sequences ---------------------------------------------------------

    def list_sequences(self) -> list[dict]:
        """List all sequences (email automations).

        Returns:
            List of sequence dicts.
        """
        return self._get("/sequences", params={"api_key": self.api_key}).get(
            "courses", []
        )

    def add_subscriber_to_sequence(
        self, sequence_id: int, email: str, **kwargs
    ) -> dict:
        """Add a subscriber to a sequence.

        Args:
            sequence_id: Sequence ID.
            email:       Subscriber email.
            kwargs:      Additional fields.

        Returns:
            Subscription dict.
        """
        data: dict = {"api_key": self.api_key, "email": email, **kwargs}
        return self._post(f"/sequences/{sequence_id}/subscribe", json=data).get(
            "subscription", {}
        )

    # -- Broadcasts --------------------------------------------------------

    def list_broadcasts(self, page: int = 1) -> list[dict]:
        """List broadcasts.

        Args:
            page: Page number.

        Returns:
            List of broadcast dicts.
        """
        return self._get(
            "/broadcasts", params={"api_secret": self.api_secret, "page": page}
        ).get("broadcasts", [])

    def create_broadcast(
        self,
        subject: str,
        content: str,
        description: str = "",
        public: bool = True,
        **kwargs,
    ) -> dict:
        """Create a broadcast (email to all subscribers).

        Args:
            subject:     Email subject line.
            content:     HTML email body.
            description: Internal description.
            public:      Whether to show on the web archive.
            kwargs:      Additional fields (send_at, email_layout_template, etc.).

        Returns:
            Created broadcast dict.
        """
        data: dict = {
            "api_secret": self.api_secret,
            "subject": subject,
            "content": content,
            "description": description,
            "public": public,
            **kwargs,
        }
        return self._post("/broadcasts", json=data).get("broadcast", {})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
