"""
SendGrid Integration — send transactional and marketing emails via the SendGrid API.

SETUP INSTRUCTIONS
==================

1. Create an account at https://sendgrid.com/ (or log in).

2. Go to Settings > API Keys:
   https://app.sendgrid.com/settings/api_keys

3. Click "Create API Key":
   - Choose "Full Access" or "Restricted Access" with at least:
     - Mail Send: Full Access
     - (Optional) Marketing: Full Access for contacts/lists

4. Copy the API key (shown only once).

5. Add to your .env:
     SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxx
     SENDGRID_FROM_EMAIL=noreply@yourdomain.com

6. Verify your sender identity:
   https://app.sendgrid.com/settings/sender_auth

IMPORTANT NOTES
===============
- API keys start with "SG.".
- You must verify a sender identity (domain or single sender) before sending.
- Rate limit: 600 requests/minute for free tier.
- API docs: https://docs.sendgrid.com/api-reference

Usage:
    from goliath.integrations.sendgrid import SendGridClient

    sg = SendGridClient()

    # Send a plain text email
    sg.send(to="user@example.com", subject="Hello", text="Plain text body")

    # Send an HTML email
    sg.send(to="user@example.com", subject="Hello", html="<h1>Hello!</h1>")

    # Send to multiple recipients
    sg.send(to=["a@example.com", "b@example.com"], subject="Update", text="News here")

    # Add a contact to a list
    sg.add_contacts(emails=["user@example.com"], list_ids=["abc-123"])
"""

import requests

from goliath import config

_API_BASE = "https://api.sendgrid.com/v3"


class SendGridClient:
    """SendGrid API client for transactional and marketing email."""

    def __init__(self):
        if not config.SENDGRID_API_KEY:
            raise RuntimeError(
                "SENDGRID_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/sendgrid.py for setup instructions."
            )
        if not config.SENDGRID_FROM_EMAIL:
            raise RuntimeError(
                "SENDGRID_FROM_EMAIL is not set. "
                "Set it to your verified sender email address."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            }
        )
        self._from_email = config.SENDGRID_FROM_EMAIL

    # -- Mail Send ---------------------------------------------------------

    def send(
        self,
        to: str | list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
    ) -> dict:
        """Send an email.

        Args:
            to:         Recipient email address(es).
            subject:    Email subject line.
            text:       Plain text body (at least one of text/html required).
            html:       HTML body.
            from_email: Override sender email (must be verified).
            from_name:  Sender display name.
            reply_to:   Reply-to email address.

        Returns:
            Empty dict on success (SendGrid returns 202 with no body).
        """
        if isinstance(to, str):
            to = [to]

        personalizations = [{"to": [{"email": addr} for addr in to]}]

        sender = {"email": from_email or self._from_email}
        if from_name:
            sender["name"] = from_name

        content = []
        if text:
            content.append({"type": "text/plain", "value": text})
        if html:
            content.append({"type": "text/html", "value": html})

        data: dict = {
            "personalizations": personalizations,
            "from": sender,
            "subject": subject,
            "content": content,
        }

        if reply_to:
            data["reply_to"] = {"email": reply_to}

        resp = self.session.post(f"{_API_BASE}/mail/send", json=data)
        resp.raise_for_status()
        return {"status": "sent"}

    def send_template(
        self,
        to: str | list[str],
        template_id: str,
        dynamic_data: dict | None = None,
        from_email: str | None = None,
    ) -> dict:
        """Send an email using a dynamic template.

        Args:
            to:           Recipient email address(es).
            template_id:  SendGrid dynamic template ID.
            dynamic_data: Template variable substitutions.
            from_email:   Override sender email.

        Returns:
            Empty dict on success.
        """
        if isinstance(to, str):
            to = [to]

        personalization: dict = {"to": [{"email": addr} for addr in to]}
        if dynamic_data:
            personalization["dynamic_template_data"] = dynamic_data

        data = {
            "personalizations": [personalization],
            "from": {"email": from_email or self._from_email},
            "template_id": template_id,
        }

        resp = self.session.post(f"{_API_BASE}/mail/send", json=data)
        resp.raise_for_status()
        return {"status": "sent"}

    # -- Contacts (Marketing) ----------------------------------------------

    def add_contacts(
        self,
        emails: list[str],
        list_ids: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Add or update contacts.

        Args:
            emails:   List of email addresses.
            list_ids: Optional list IDs to add contacts to.
            kwargs:   Additional contact fields (first_name, last_name, etc.).

        Returns:
            Job status dict.
        """
        contacts = [{"email": email, **kwargs} for email in emails]
        data: dict = {"contacts": contacts}
        if list_ids:
            data["list_ids"] = list_ids
        return self._put("/marketing/contacts", json=data)

    def list_contacts(self) -> list[dict]:
        """Export all contacts (async — returns job info).

        Returns:
            Contact export job dict.
        """
        return self._post("/marketing/contacts/exports", json={})

    def search_contacts(self, query: str) -> list[dict]:
        """Search contacts using SGQL.

        Args:
            query: SGQL query (e.g. "email LIKE '%@example.com'").

        Returns:
            List of matching contact dicts.
        """
        resp = self._post("/marketing/contacts/search", json={"query": query})
        return resp.get("result", [])

    # -- Lists -------------------------------------------------------------

    def list_lists(self) -> list[dict]:
        """List all contact lists.

        Returns:
            List of list dicts.
        """
        return self._get("/marketing/lists").get("result", [])

    def create_list(self, name: str) -> dict:
        """Create a contact list.

        Args:
            name: List name.

        Returns:
            Created list dict.
        """
        return self._post("/marketing/lists", json={"name": name})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 202 or not resp.content:
            return {"status": "accepted"}
        return resp.json()

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 202 or not resp.content:
            return {"status": "accepted"}
        return resp.json()
