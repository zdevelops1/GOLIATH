"""
Mailchimp Integration — manage audiences, campaigns, and subscribers via the Mailchimp API.

SETUP INSTRUCTIONS
==================

1. Log in to https://mailchimp.com/

2. Go to Account > Extras > API keys:
   https://us1.admin.mailchimp.com/account/api/

3. Click "Create A Key" and copy it.

4. Your API key looks like: xxxxxxxxxxxxxxxx-us14
   The suffix (e.g. "us14") is your data center.

5. Add to your .env:
     MAILCHIMP_API_KEY=xxxxxxxxxxxxxxxx-us14
     MAILCHIMP_SERVER_PREFIX=us14

   The server prefix is the part after the dash in your API key.

IMPORTANT NOTES
===============
- The server prefix determines the API endpoint (e.g. us14.api.mailchimp.com).
- Rate limit: 10 simultaneous connections per user.
- Audience/list IDs can be found in Audience > Settings > Audience name and defaults.
- API docs: https://mailchimp.com/developer/marketing/api/

Usage:
    from goliath.integrations.mailchimp import MailchimpClient

    mc = MailchimpClient()

    # List audiences
    audiences = mc.list_audiences()

    # Add a subscriber
    mc.add_subscriber(list_id="abc123", email="user@example.com", first_name="Jane")

    # Create a campaign
    campaign = mc.create_campaign(list_id="abc123", subject="Newsletter", from_name="GOLIATH")

    # Send a campaign
    mc.send_campaign(campaign_id="xyz789")
"""

import hashlib

import requests

from goliath import config


class MailchimpClient:
    """Mailchimp Marketing API client for audiences, campaigns, and subscribers."""

    def __init__(self):
        if not config.MAILCHIMP_API_KEY:
            raise RuntimeError(
                "MAILCHIMP_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/mailchimp.py for setup instructions."
            )
        if not config.MAILCHIMP_SERVER_PREFIX:
            raise RuntimeError(
                "MAILCHIMP_SERVER_PREFIX is not set (e.g. 'us14'). "
                "It's the suffix after the dash in your API key."
            )

        self._base = f"https://{config.MAILCHIMP_SERVER_PREFIX}.api.mailchimp.com/3.0"
        self.session = requests.Session()
        self.session.auth = ("anystring", config.MAILCHIMP_API_KEY)
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Audiences (Lists) -------------------------------------------------

    def list_audiences(self, count: int = 10) -> list[dict]:
        """List audiences (mailing lists).

        Args:
            count: Number of audiences to return.

        Returns:
            List of audience dicts.
        """
        return self._get("/lists", params={"count": count}).get("lists", [])

    def get_audience(self, list_id: str) -> dict:
        """Get a single audience by ID.

        Args:
            list_id: Mailchimp audience/list ID.

        Returns:
            Audience dict.
        """
        return self._get(f"/lists/{list_id}")

    # -- Subscribers (Members) ---------------------------------------------

    def add_subscriber(
        self,
        list_id: str,
        email: str,
        status: str = "subscribed",
        first_name: str | None = None,
        last_name: str | None = None,
        **kwargs,
    ) -> dict:
        """Add a subscriber to an audience.

        Args:
            list_id:    Audience/list ID.
            email:      Subscriber email address.
            status:     "subscribed", "unsubscribed", "pending", or "cleaned".
            first_name: Subscriber first name.
            last_name:  Subscriber last name.
            kwargs:     Additional fields (tags, language, etc.).

        Returns:
            Subscriber dict.
        """
        merge_fields = {}
        if first_name:
            merge_fields["FNAME"] = first_name
        if last_name:
            merge_fields["LNAME"] = last_name

        data = {
            "email_address": email,
            "status": status,
            **kwargs,
        }
        if merge_fields:
            data["merge_fields"] = merge_fields

        return self._post(f"/lists/{list_id}/members", json=data)

    def get_subscriber(self, list_id: str, email: str) -> dict:
        """Get a subscriber by email.

        Args:
            list_id: Audience/list ID.
            email:   Subscriber email address.

        Returns:
            Subscriber dict.
        """
        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
        return self._get(f"/lists/{list_id}/members/{subscriber_hash}")

    def update_subscriber(self, list_id: str, email: str, **kwargs) -> dict:
        """Update a subscriber.

        Args:
            list_id: Audience/list ID.
            email:   Subscriber email address.
            kwargs:  Fields to update (status, merge_fields, tags, etc.).

        Returns:
            Updated subscriber dict.
        """
        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
        return self._patch(f"/lists/{list_id}/members/{subscriber_hash}", json=kwargs)

    def delete_subscriber(self, list_id: str, email: str) -> None:
        """Permanently delete a subscriber.

        Args:
            list_id: Audience/list ID.
            email:   Subscriber email address.
        """
        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
        resp = self.session.delete(
            f"{self._base}/lists/{list_id}/members/{subscriber_hash}"
        )
        resp.raise_for_status()

    def list_subscribers(
        self, list_id: str, count: int = 10, status: str | None = None
    ) -> list[dict]:
        """List subscribers in an audience.

        Args:
            list_id: Audience/list ID.
            count:   Number of subscribers to return.
            status:  Filter by status (subscribed, unsubscribed, etc.).

        Returns:
            List of subscriber dicts.
        """
        params: dict = {"count": count}
        if status:
            params["status"] = status
        return self._get(f"/lists/{list_id}/members", params=params).get("members", [])

    # -- Campaigns ---------------------------------------------------------

    def create_campaign(
        self,
        list_id: str,
        subject: str,
        from_name: str,
        reply_to: str | None = None,
        campaign_type: str = "regular",
    ) -> dict:
        """Create an email campaign.

        Args:
            list_id:       Audience/list ID to send to.
            subject:       Email subject line.
            from_name:     Sender name.
            reply_to:      Reply-to email (defaults to account email).
            campaign_type: "regular", "plaintext", "absplit", or "rss".

        Returns:
            Campaign dict with id and web_id.
        """
        data = {
            "type": campaign_type,
            "recipients": {"list_id": list_id},
            "settings": {
                "subject_line": subject,
                "from_name": from_name,
            },
        }
        if reply_to:
            data["settings"]["reply_to"] = reply_to
        return self._post("/campaigns", json=data)

    def set_campaign_content(self, campaign_id: str, html: str) -> dict:
        """Set the HTML content for a campaign.

        Args:
            campaign_id: Mailchimp campaign ID.
            html:        Full HTML content for the email.

        Returns:
            Content dict.
        """
        return self._put(f"/campaigns/{campaign_id}/content", json={"html": html})

    def send_campaign(self, campaign_id: str) -> None:
        """Send a campaign.

        Args:
            campaign_id: Mailchimp campaign ID.
        """
        resp = self.session.post(f"{self._base}/campaigns/{campaign_id}/actions/send")
        resp.raise_for_status()

    def list_campaigns(self, count: int = 10, status: str | None = None) -> list[dict]:
        """List campaigns.

        Args:
            count:  Number of campaigns to return.
            status: Filter by status ("save", "paused", "schedule", "sending", "sent").

        Returns:
            List of campaign dicts.
        """
        params: dict = {"count": count}
        if status:
            params["status"] = status
        return self._get("/campaigns", params=params).get("campaigns", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, **kwargs) -> dict:
        resp = self.session.patch(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
