"""
Zendesk Integration — manage tickets, users, and organizations via the Zendesk Support API.

SETUP INSTRUCTIONS
==================

1. Log in to your Zendesk Support instance (e.g. https://yourcompany.zendesk.com/).

2. Go to Admin Center > Apps and integrations > Zendesk API.

3. Enable Token Access and click "Add API token".

4. Copy the token and add to your .env:
     ZENDESK_SUBDOMAIN=yourcompany
     ZENDESK_EMAIL=agent@yourcompany.com
     ZENDESK_API_TOKEN=xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses email/token Basic auth ({email}/token:{api_token}).
- API docs: https://developer.zendesk.com/api-reference/
- Rate limit: 700 requests per minute (Team/Professional plans).
- Pagination: results are paginated; this client returns the first page by default.

Usage:
    from goliath.integrations.zendesk import ZendeskClient

    zd = ZendeskClient()

    # Create a ticket
    ticket = zd.create_ticket(
        subject="Cannot log in",
        description="User reports 403 error on login page.",
        priority="high",
    )

    # Get a ticket
    ticket = zd.get_ticket(12345)

    # Update a ticket
    zd.update_ticket(12345, status="pending", assignee_id=9876)

    # Search tickets
    results = zd.search_tickets("status:open type:ticket priority:high")

    # Add a comment to a ticket
    zd.add_comment(12345, body="Investigating now.", public=True)

    # List ticket fields
    fields = zd.list_ticket_fields()
"""

import requests

from goliath import config


class ZendeskClient:
    """Zendesk Support REST API client for tickets, users, and organizations."""

    def __init__(self):
        if not config.ZENDESK_API_TOKEN:
            raise RuntimeError(
                "ZENDESK_API_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/zendesk.py for setup instructions."
            )
        if not config.ZENDESK_EMAIL:
            raise RuntimeError(
                "ZENDESK_EMAIL is not set. Add your Zendesk agent email to .env."
            )
        if not config.ZENDESK_SUBDOMAIN:
            raise RuntimeError(
                "ZENDESK_SUBDOMAIN is not set (e.g. 'yourcompany'). "
                "Add it to .env."
            )

        self._base = f"https://{config.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"
        self.session = requests.Session()
        self.session.auth = (f"{config.ZENDESK_EMAIL}/token", config.ZENDESK_API_TOKEN)
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Tickets -----------------------------------------------------------

    def create_ticket(
        self,
        subject: str,
        description: str,
        priority: str | None = None,
        requester_email: str | None = None,
        tags: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Create a new ticket.

        Args:
            subject:         Ticket subject line.
            description:     Ticket description / first comment body.
            priority:        "low", "normal", "high", or "urgent".
            requester_email: Email of the requester (creates user if needed).
            tags:            List of tag strings.
            kwargs:          Additional ticket fields.

        Returns:
            Created ticket dict.
        """
        ticket: dict = {"subject": subject, "comment": {"body": description}, **kwargs}
        if priority:
            ticket["priority"] = priority
        if requester_email:
            ticket["requester"] = {"email": requester_email}
        if tags:
            ticket["tags"] = tags
        return self._post("/tickets.json", json={"ticket": ticket}).get("ticket", {})

    def get_ticket(self, ticket_id: int) -> dict:
        """Get a ticket by ID.

        Args:
            ticket_id: Ticket ID.

        Returns:
            Ticket dict.
        """
        return self._get(f"/tickets/{ticket_id}.json").get("ticket", {})

    def update_ticket(self, ticket_id: int, **kwargs) -> dict:
        """Update a ticket's fields.

        Args:
            ticket_id: Ticket ID.
            kwargs:    Fields to update (status, priority, assignee_id, tags, etc.).

        Returns:
            Updated ticket dict.
        """
        resp = self.session.put(
            f"{self._base}/tickets/{ticket_id}.json",
            json={"ticket": kwargs},
        )
        resp.raise_for_status()
        return resp.json().get("ticket", {})

    def delete_ticket(self, ticket_id: int) -> None:
        """Delete a ticket.

        Args:
            ticket_id: Ticket ID.
        """
        resp = self.session.delete(f"{self._base}/tickets/{ticket_id}.json")
        resp.raise_for_status()

    def list_tickets(self, page: int = 1, per_page: int = 100) -> list[dict]:
        """List tickets.

        Args:
            page:     Page number.
            per_page: Results per page (max 100).

        Returns:
            List of ticket dicts.
        """
        return self._get(
            "/tickets.json", params={"page": page, "per_page": per_page}
        ).get("tickets", [])

    def search_tickets(self, query: str) -> list[dict]:
        """Search tickets using Zendesk search syntax.

        Args:
            query: Search query (e.g. "status:open type:ticket priority:high").

        Returns:
            List of matching result dicts.
        """
        return self._get("/search.json", params={"query": query}).get("results", [])

    # -- Comments ----------------------------------------------------------

    def add_comment(
        self,
        ticket_id: int,
        body: str,
        public: bool = True,
        author_id: int | None = None,
    ) -> dict:
        """Add a comment to a ticket.

        Args:
            ticket_id: Ticket ID.
            body:      Comment text.
            public:    Whether the comment is visible to the requester.
            author_id: Optional author user ID.

        Returns:
            Updated ticket dict.
        """
        comment: dict = {"body": body, "public": public}
        if author_id:
            comment["author_id"] = author_id
        return self.update_ticket(ticket_id, comment=comment)

    def get_comments(self, ticket_id: int) -> list[dict]:
        """Get all comments on a ticket.

        Args:
            ticket_id: Ticket ID.

        Returns:
            List of comment dicts.
        """
        return self._get(f"/tickets/{ticket_id}/comments.json").get("comments", [])

    # -- Users -------------------------------------------------------------

    def create_user(self, name: str, email: str, **kwargs) -> dict:
        """Create a user.

        Args:
            name:   User name.
            email:  User email.
            kwargs: Additional fields (role, phone, etc.).

        Returns:
            Created user dict.
        """
        return self._post(
            "/users.json", json={"user": {"name": name, "email": email, **kwargs}}
        ).get("user", {})

    def get_user(self, user_id: int) -> dict:
        """Get a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User dict.
        """
        return self._get(f"/users/{user_id}.json").get("user", {})

    # -- Ticket Fields -----------------------------------------------------

    def list_ticket_fields(self) -> list[dict]:
        """List all ticket fields.

        Returns:
            List of ticket field dicts.
        """
        return self._get("/ticket_fields.json").get("ticket_fields", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
