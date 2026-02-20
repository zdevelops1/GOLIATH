"""
Resend Integration — send transactional emails via the Resend API.

SETUP INSTRUCTIONS
==================

1. Sign up at https://resend.com/ and log in.

2. Go to API Keys (https://resend.com/api-keys).

3. Click "Create API Key", give it a name (e.g. "GOLIATH").

4. Copy the key and add it to your .env:
     RESEND_API_KEY=re_xxxxxxxxxxxxxxxx

5. You must also verify a sending domain under Domains in the dashboard,
   or use the free "onboarding@resend.dev" for testing.

IMPORTANT NOTES
===============
- Authentication uses an API key (Bearer token).
- API docs: https://resend.com/docs/api-reference
- Rate limit: 10 emails per second (free tier: 100 emails/day).
- Supports HTML and plain text emails, attachments, tags, and scheduling.
- From address must use a verified domain.

Usage:
    from goliath.integrations.resend import ResendClient

    rs = ResendClient()

    # Send an email
    email = rs.send(
        from_addr="you@yourdomain.com",
        to=["user@example.com"],
        subject="Hello from GOLIATH",
        html="<h1>Hello!</h1><p>This email was sent by GOLIATH.</p>",
    )

    # Send with plain text
    rs.send(
        from_addr="you@yourdomain.com",
        to=["user@example.com"],
        subject="Plain text email",
        text="Hello! This is plain text.",
    )

    # Send with CC, BCC, reply-to
    rs.send(
        from_addr="you@yourdomain.com",
        to=["user@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        reply_to="support@yourdomain.com",
        subject="Team update",
        html="<p>Update content here.</p>",
    )

    # Get an email by ID
    email = rs.get_email("email_id")

    # List domains
    domains = rs.list_domains()

    # List API keys
    keys = rs.list_api_keys()
"""

import requests

from goliath import config

_API_BASE = "https://api.resend.com"


class ResendClient:
    """Resend API client for transactional email."""

    def __init__(self):
        if not config.RESEND_API_KEY:
            raise RuntimeError(
                "RESEND_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/resend.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.RESEND_API_KEY}",
            "Content-Type": "application/json",
        })

    # -- Emails ------------------------------------------------------------

    def send(
        self,
        from_addr: str,
        to: list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        tags: list[dict] | None = None,
        attachments: list[dict] | None = None,
        scheduled_at: str | None = None,
        **kwargs,
    ) -> dict:
        """Send an email.

        Args:
            from_addr:    Sender address (must use a verified domain).
            to:           List of recipient addresses.
            subject:      Email subject.
            html:         HTML body.
            text:         Plain text body.
            cc:           CC recipients.
            bcc:          BCC recipients.
            reply_to:     Reply-to address.
            tags:         List of tag dicts [{"name": "category", "value": "welcome"}].
            attachments:  List of attachment dicts [{"filename": "f.pdf", "content": "base64..."}].
            scheduled_at: ISO 8601 datetime to schedule the email.
            kwargs:       Additional fields (headers, etc.).

        Returns:
            Dict with "id" of the sent email.
        """
        data: dict = {
            "from": from_addr,
            "to": to,
            "subject": subject,
            **kwargs,
        }
        if html:
            data["html"] = html
        if text:
            data["text"] = text
        if cc:
            data["cc"] = cc
        if bcc:
            data["bcc"] = bcc
        if reply_to:
            data["reply_to"] = reply_to
        if tags:
            data["tags"] = tags
        if attachments:
            data["attachments"] = attachments
        if scheduled_at:
            data["scheduled_at"] = scheduled_at
        return self._post("/emails", json=data)

    def send_batch(self, emails: list[dict]) -> list[dict]:
        """Send a batch of emails.

        Args:
            emails: List of email dicts (each matching the send() params).

        Returns:
            List of result dicts with "id" for each email.
        """
        return self._post("/emails/batch", json=emails)

    def get_email(self, email_id: str) -> dict:
        """Get an email by ID.

        Args:
            email_id: Email ID.

        Returns:
            Email dict with status, to, subject, etc.
        """
        return self._get(f"/emails/{email_id}")

    # -- Domains -----------------------------------------------------------

    def list_domains(self) -> list[dict]:
        """List verified sending domains.

        Returns:
            List of domain dicts.
        """
        return self._get("/domains").get("data", [])

    def get_domain(self, domain_id: str) -> dict:
        """Get a domain by ID.

        Args:
            domain_id: Domain ID.

        Returns:
            Domain dict with records and verification status.
        """
        return self._get(f"/domains/{domain_id}")

    def create_domain(self, name: str, region: str = "us-east-1") -> dict:
        """Add a domain for sending.

        Args:
            name:   Domain name (e.g. "yourdomain.com").
            region: AWS region for the sending infrastructure.

        Returns:
            Created domain dict with DNS records to configure.
        """
        return self._post("/domains", json={"name": name, "region": region})

    def verify_domain(self, domain_id: str) -> dict:
        """Trigger domain verification.

        Args:
            domain_id: Domain ID.

        Returns:
            Verification result dict.
        """
        return self._post(f"/domains/{domain_id}/verify")

    def delete_domain(self, domain_id: str) -> None:
        """Delete a domain.

        Args:
            domain_id: Domain ID.
        """
        resp = self.session.delete(f"{_API_BASE}/domains/{domain_id}")
        resp.raise_for_status()

    # -- API Keys ----------------------------------------------------------

    def list_api_keys(self) -> list[dict]:
        """List API keys.

        Returns:
            List of API key dicts (id, name, created_at).
        """
        return self._get("/api-keys").get("data", [])

    def create_api_key(self, name: str, permission: str = "full_access") -> dict:
        """Create an API key.

        Args:
            name:       Key name.
            permission: "full_access" or "sending_access".

        Returns:
            Dict with "id" and "token".
        """
        return self._post(
            "/api-keys", json={"name": name, "permission": permission}
        )

    def delete_api_key(self, key_id: str) -> None:
        """Delete an API key.

        Args:
            key_id: API key ID.
        """
        resp = self.session.delete(f"{_API_BASE}/api-keys/{key_id}")
        resp.raise_for_status()

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
