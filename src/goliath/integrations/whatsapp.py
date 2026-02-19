"""
WhatsApp Integration — send messages via the WhatsApp Cloud API.

SETUP INSTRUCTIONS
==================

1. Create a Meta Developer account at https://developers.facebook.com

2. Create a new app (type: Business) in the Meta App Dashboard.

3. Add the "WhatsApp" product to your app.

4. In the WhatsApp section, go to "API Setup":
   - You'll see a temporary access token and a test phone number.
   - The Phone Number ID is displayed under the test number.
   - For production, add and verify your own phone number.

5. Add a recipient phone number to the "To" field and click "Send Message"
   to verify connectivity.

6. For a permanent access token, create a System User in Business Settings:
   - Go to Business Settings > System Users > Add.
   - Assign the app to the system user with full control.
   - Generate a token with whatsapp_business_messaging permission.

7. Add credentials to your .env:
     WHATSAPP_PHONE_ID=123456789012345
     WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Recipients must have opted in or initiated a conversation first.
- Template messages can be sent to any opted-in user (no 24-hour window).
- Free-form messages require an active 24-hour conversation window
  (opened when the user messages you first).
- Rate limits vary by tier. New accounts start at Tier 1 (1K conversations/day).

Usage:
    from goliath.integrations.whatsapp import WhatsAppClient

    wa = WhatsAppClient()

    # Send a text message
    wa.send_text(to="15551234567", body="Hello from GOLIATH!")

    # Send an image
    wa.send_image(to="15551234567", image_url="https://example.com/photo.jpg")

    # Send a template message
    wa.send_template(to="15551234567", template_name="hello_world", language="en_US")

    # Send a location
    wa.send_location(to="15551234567", latitude=37.7749, longitude=-122.4194, name="San Francisco")
"""

import requests

from goliath import config

_API_VERSION = "v21.0"
_BASE_URL = f"https://graph.facebook.com/{_API_VERSION}"


class WhatsAppClient:
    """WhatsApp Cloud API client for sending messages."""

    def __init__(self):
        if not config.WHATSAPP_ACCESS_TOKEN:
            raise RuntimeError(
                "WHATSAPP_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/whatsapp.py for setup instructions."
            )
        if not config.WHATSAPP_PHONE_ID:
            raise RuntimeError(
                "WHATSAPP_PHONE_ID is not set. "
                "Add it to .env or export as an environment variable."
            )

        self.phone_id = config.WHATSAPP_PHONE_ID
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- public API --------------------------------------------------------

    def send_text(self, to: str, body: str, preview_url: bool = False) -> dict:
        """Send a text message.

        Args:
            to:          Recipient phone number with country code (e.g. "15551234567").
            body:        Message text (up to 4096 characters).
            preview_url: Whether to show a URL preview if the body contains a link.

        Returns:
            API response dict with message ID.
        """
        return self._send(
            to,
            {
                "type": "text",
                "text": {"body": body, "preview_url": preview_url},
            },
        )

    def send_image(
        self,
        to: str,
        image_url: str | None = None,
        image_id: str | None = None,
        caption: str = "",
    ) -> dict:
        """Send an image message.

        Provide either image_url (publicly accessible) or image_id
        (previously uploaded media ID).

        Args:
            to:        Recipient phone number.
            image_url: Public URL to the image.
            image_id:  WhatsApp media ID.
            caption:   Optional image caption.

        Returns:
            API response dict.
        """
        image: dict = {}
        if image_url:
            image["link"] = image_url
        elif image_id:
            image["id"] = image_id
        else:
            raise ValueError("Provide image_url or image_id.")
        if caption:
            image["caption"] = caption
        return self._send(to, {"type": "image", "image": image})

    def send_document(
        self,
        to: str,
        document_url: str | None = None,
        document_id: str | None = None,
        caption: str = "",
        filename: str = "",
    ) -> dict:
        """Send a document message.

        Args:
            to:           Recipient phone number.
            document_url: Public URL to the document.
            document_id:  WhatsApp media ID.
            caption:      Optional caption.
            filename:     Display filename for the document.

        Returns:
            API response dict.
        """
        doc: dict = {}
        if document_url:
            doc["link"] = document_url
        elif document_id:
            doc["id"] = document_id
        else:
            raise ValueError("Provide document_url or document_id.")
        if caption:
            doc["caption"] = caption
        if filename:
            doc["filename"] = filename
        return self._send(to, {"type": "document", "document": doc})

    def send_audio(
        self,
        to: str,
        audio_url: str | None = None,
        audio_id: str | None = None,
    ) -> dict:
        """Send an audio message.

        Args:
            to:        Recipient phone number.
            audio_url: Public URL to the audio file.
            audio_id:  WhatsApp media ID.

        Returns:
            API response dict.
        """
        audio: dict = {}
        if audio_url:
            audio["link"] = audio_url
        elif audio_id:
            audio["id"] = audio_id
        else:
            raise ValueError("Provide audio_url or audio_id.")
        return self._send(to, {"type": "audio", "audio": audio})

    def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en_US",
        components: list[dict] | None = None,
    ) -> dict:
        """Send a template message.

        Template messages can be sent outside the 24-hour conversation window.

        Args:
            to:            Recipient phone number.
            template_name: Name of the approved message template.
            language:      Language code (e.g. "en_US").
            components:    Optional template component parameters.

        Returns:
            API response dict.
        """
        template: dict = {
            "name": template_name,
            "language": {"code": language},
        }
        if components:
            template["components"] = components
        return self._send(to, {"type": "template", "template": template})

    def send_location(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: str = "",
        address: str = "",
    ) -> dict:
        """Send a location message.

        Args:
            to:        Recipient phone number.
            latitude:  Location latitude.
            longitude: Location longitude.
            name:      Optional location name.
            address:   Optional street address.

        Returns:
            API response dict.
        """
        location: dict = {
            "latitude": str(latitude),
            "longitude": str(longitude),
        }
        if name:
            location["name"] = name
        if address:
            location["address"] = address
        return self._send(to, {"type": "location", "location": location})

    # -- internal helpers --------------------------------------------------

    def _send(self, to: str, message: dict) -> dict:
        """Send a message payload to a recipient."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            **message,
        }
        resp = self.session.post(
            f"{_BASE_URL}/{self.phone_id}/messages",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
