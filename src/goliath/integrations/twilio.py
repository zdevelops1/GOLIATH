"""
Twilio SMS Integration — send and manage SMS/MMS messages via the Twilio REST API.

SETUP INSTRUCTIONS
==================

1. Create a Twilio account at https://www.twilio.com/try-twilio

2. From the Twilio Console (https://console.twilio.com/):
   - Copy your Account SID and Auth Token from the dashboard.
   - Get a Twilio phone number (Messaging > Try it out > Get a number,
     or Phone Numbers > Manage > Buy a number).

3. Add to your .env:
     TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     TWILIO_AUTH_TOKEN=your-auth-token
     TWILIO_PHONE_NUMBER=+15551234567

IMPORTANT NOTES
===============
- Trial accounts can only send to verified phone numbers.
- Phone numbers must be in E.164 format (e.g. "+15551234567").
- MMS is supported in the US and Canada (attach images via media_url).
- Rate limits vary by number type: ~1 msg/sec for long codes,
  ~30 msg/sec for toll-free, higher for short codes.
- Pricing varies by destination country.

Usage:
    from goliath.integrations.twilio import TwilioClient

    sms = TwilioClient()

    # Send a text message
    sms.send(to="+15559876543", body="Hello from GOLIATH!")

    # Send an MMS with an image
    sms.send(to="+15559876543", body="Check this out!", media_url="https://example.com/photo.jpg")

    # Get message details
    msg = sms.get_message("SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    # List recent messages
    messages = sms.list_messages(limit=10)
"""

import requests

from goliath import config

_API_BASE = "https://api.twilio.com/2010-04-01"


class TwilioClient:
    """Twilio REST API client for SMS and MMS messaging."""

    def __init__(self):
        creds = {
            "TWILIO_ACCOUNT_SID": config.TWILIO_ACCOUNT_SID,
            "TWILIO_AUTH_TOKEN": config.TWILIO_AUTH_TOKEN,
            "TWILIO_PHONE_NUMBER": config.TWILIO_PHONE_NUMBER,
        }
        missing = [k for k, v in creds.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing Twilio credentials: {', '.join(missing)}. "
                "Add them to .env or export as environment variables. "
                "See integrations/twilio.py for setup instructions."
            )

        self._sid = config.TWILIO_ACCOUNT_SID
        self._from = config.TWILIO_PHONE_NUMBER
        self._base = f"{_API_BASE}/Accounts/{self._sid}"
        self.session = requests.Session()
        self.session.auth = (self._sid, config.TWILIO_AUTH_TOKEN)

    # -- public API --------------------------------------------------------

    def send(
        self,
        to: str,
        body: str,
        media_url: str | None = None,
        from_number: str | None = None,
    ) -> dict:
        """Send an SMS or MMS message.

        Args:
            to:          Recipient phone number in E.164 format.
            body:        Message text (up to 1,600 characters).
            media_url:   Optional URL to an image for MMS.
            from_number: Override the default sender number.

        Returns:
            Twilio message resource dict.
        """
        data: dict = {
            "To": to,
            "From": from_number or self._from,
            "Body": body,
        }
        if media_url:
            data["MediaUrl"] = media_url

        resp = self.session.post(
            f"{self._base}/Messages.json",
            data=data,
        )
        resp.raise_for_status()
        return resp.json()

    def get_message(self, message_sid: str) -> dict:
        """Get details about a sent message.

        Args:
            message_sid: Twilio message SID (e.g. "SMxxx").

        Returns:
            Message resource dict with status, price, etc.
        """
        resp = self.session.get(f"{self._base}/Messages/{message_sid}.json")
        resp.raise_for_status()
        return resp.json()

    def list_messages(
        self,
        limit: int = 20,
        to: str | None = None,
        from_number: str | None = None,
        date_sent: str | None = None,
    ) -> list[dict]:
        """List sent and received messages.

        Args:
            limit:       Number of messages (1–1000).
            to:          Filter by recipient number.
            from_number: Filter by sender number.
            date_sent:   Filter by date (YYYY-MM-DD).

        Returns:
            List of message resource dicts.
        """
        params: dict = {"PageSize": limit}
        if to:
            params["To"] = to
        if from_number:
            params["From"] = from_number
        if date_sent:
            params["DateSent"] = date_sent

        resp = self.session.get(f"{self._base}/Messages.json", params=params)
        resp.raise_for_status()
        return resp.json().get("messages", [])

    def delete_message(self, message_sid: str) -> None:
        """Delete a message from Twilio logs.

        Args:
            message_sid: Twilio message SID.
        """
        resp = self.session.delete(f"{self._base}/Messages/{message_sid}.json")
        resp.raise_for_status()
