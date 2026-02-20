"""
Intercom Integration — manage contacts, conversations, and messages via the Intercom API.

SETUP INSTRUCTIONS
==================

1. Log in to Intercom at https://app.intercom.com/

2. Go to Settings > Integrations > Developer Hub (or visit
   https://app.intercom.com/a/apps/_/developer-hub).

3. Create a new app or select an existing one.

4. Go to Authentication and copy the Access Token.

5. Add it to your .env:
     INTERCOM_ACCESS_TOKEN=dG9rOjEyMzQ1Njc4...

IMPORTANT NOTES
===============
- Authentication uses a Bearer token.
- API docs: https://developers.intercom.com/docs/references/rest-api/api.intercom.io/
- Rate limit: ~1000 requests per minute.
- API version is set via the Intercom-Version header (this client uses 2.10).

Usage:
    from goliath.integrations.intercom import IntercomClient

    ic = IntercomClient()

    # Create a contact (lead or user)
    contact = ic.create_contact(role="user", email="jane@example.com", name="Jane Doe")

    # Get a contact
    contact = ic.get_contact("6001abcd")

    # Search contacts by email
    results = ic.search_contacts(field="email", value="jane@example.com")

    # Send a message
    ic.send_message(
        from_admin_id="12345",
        to_contact_id="6001abcd",
        body="Hi Jane, how can we help?",
    )

    # List conversations
    conversations = ic.list_conversations()

    # Reply to a conversation
    ic.reply_to_conversation(
        conversation_id="99887766",
        admin_id="12345",
        body="Thanks for reaching out! We're looking into it.",
    )

    # Create a note on a contact
    ic.create_note(contact_id="6001abcd", admin_id="12345", body="VIP customer.")
"""

import requests

from goliath import config

_API_BASE = "https://api.intercom.io"
_API_VERSION = "2.10"


class IntercomClient:
    """Intercom REST API client for contacts, conversations, and messaging."""

    def __init__(self):
        if not config.INTERCOM_ACCESS_TOKEN:
            raise RuntimeError(
                "INTERCOM_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/intercom.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.INTERCOM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": _API_VERSION,
        })

    # -- Contacts ----------------------------------------------------------

    def create_contact(
        self,
        role: str = "user",
        email: str | None = None,
        name: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a contact (user or lead).

        Args:
            role:   "user" or "lead".
            email:  Contact email.
            name:   Contact name.
            kwargs: Additional fields (phone, custom_attributes, etc.).

        Returns:
            Created contact dict.
        """
        data: dict = {"role": role, **kwargs}
        if email:
            data["email"] = email
        if name:
            data["name"] = name
        return self._post("/contacts", json=data)

    def get_contact(self, contact_id: str) -> dict:
        """Get a contact by ID.

        Args:
            contact_id: Intercom contact ID.

        Returns:
            Contact dict.
        """
        return self._get(f"/contacts/{contact_id}")

    def update_contact(self, contact_id: str, **kwargs) -> dict:
        """Update a contact's fields.

        Args:
            contact_id: Intercom contact ID.
            kwargs:     Fields to update (name, email, phone, custom_attributes, etc.).

        Returns:
            Updated contact dict.
        """
        resp = self.session.put(f"{_API_BASE}/contacts/{contact_id}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def search_contacts(
        self, field: str, value: str, operator: str = "="
    ) -> list[dict]:
        """Search contacts by a single field.

        Args:
            field:    Field name (e.g. "email", "name", "role").
            value:    Value to match.
            operator: Comparison operator ("=", "!=", "~", etc.).

        Returns:
            List of matching contact dicts.
        """
        payload = {
            "query": {
                "field": field,
                "operator": operator,
                "value": value,
            }
        }
        return self._post("/contacts/search", json=payload).get("data", [])

    def list_contacts(self, per_page: int = 50) -> list[dict]:
        """List contacts.

        Args:
            per_page: Results per page (max 150).

        Returns:
            List of contact dicts.
        """
        return self._get("/contacts", params={"per_page": per_page}).get("data", [])

    # -- Conversations -----------------------------------------------------

    def list_conversations(self, per_page: int = 20) -> list[dict]:
        """List conversations.

        Args:
            per_page: Results per page.

        Returns:
            List of conversation dicts.
        """
        return self._get("/conversations", params={"per_page": per_page}).get(
            "conversations", []
        )

    def get_conversation(self, conversation_id: str) -> dict:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID.

        Returns:
            Conversation dict with parts.
        """
        return self._get(f"/conversations/{conversation_id}")

    def reply_to_conversation(
        self,
        conversation_id: str,
        admin_id: str,
        body: str,
        message_type: str = "comment",
    ) -> dict:
        """Reply to a conversation as an admin.

        Args:
            conversation_id: Conversation ID.
            admin_id:        Admin ID sending the reply.
            body:            Reply body text.
            message_type:    "comment" or "note".

        Returns:
            Conversation dict.
        """
        return self._post(
            f"/conversations/{conversation_id}/reply",
            json={
                "message_type": message_type,
                "type": "admin",
                "admin_id": admin_id,
                "body": body,
            },
        )

    # -- Messages ----------------------------------------------------------

    def send_message(
        self,
        from_admin_id: str,
        to_contact_id: str,
        body: str,
        message_type: str = "inapp",
    ) -> dict:
        """Send a message from an admin to a contact.

        Args:
            from_admin_id: Admin ID.
            to_contact_id: Contact ID.
            body:          Message body.
            message_type:  "inapp" or "email".

        Returns:
            Created message dict.
        """
        return self._post(
            "/messages",
            json={
                "message_type": message_type,
                "body": body,
                "from": {"type": "admin", "id": from_admin_id},
                "to": {"type": "user", "id": to_contact_id},
            },
        )

    # -- Notes -------------------------------------------------------------

    def create_note(self, contact_id: str, admin_id: str, body: str) -> dict:
        """Create a note on a contact.

        Args:
            contact_id: Contact ID.
            admin_id:   Admin ID authoring the note.
            body:       Note body text.

        Returns:
            Created note dict.
        """
        return self._post(
            f"/contacts/{contact_id}/notes",
            json={"admin_id": admin_id, "body": body},
        )

    # -- Tags --------------------------------------------------------------

    def list_tags(self) -> list[dict]:
        """List all tags.

        Returns:
            List of tag dicts.
        """
        return self._get("/tags").get("data", [])

    def tag_contact(self, contact_id: str, tag_id: str) -> dict:
        """Tag a contact.

        Args:
            contact_id: Contact ID.
            tag_id:     Tag ID.

        Returns:
            Tag dict.
        """
        return self._post(
            f"/contacts/{contact_id}/tags", json={"id": tag_id}
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
