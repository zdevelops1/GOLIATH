"""
PayPal Integration — manage orders, payments, and payouts via the PayPal REST API v2.

SETUP INSTRUCTIONS
==================

1. Go to https://developer.paypal.com/ and log in.

2. Go to Apps & Credentials (Dashboard > My Apps & Credentials).

3. Create a new REST API app (or use the default Sandbox app).
   - Note the Client ID and Secret.

4. Toggle between Sandbox (testing) and Live (production) as needed.

5. Add to your .env:
     PAYPAL_CLIENT_ID=your-client-id
     PAYPAL_CLIENT_SECRET=your-client-secret
     PAYPAL_SANDBOX=true

   Set PAYPAL_SANDBOX=false for live/production transactions.

IMPORTANT NOTES
===============
- Sandbox mode uses https://api-m.sandbox.paypal.com
- Live mode uses https://api-m.paypal.com
- Authentication uses OAuth 2.0 client credentials flow.
- Amounts include currency_code (e.g. "USD") and value (e.g. "10.00").
- Orders follow the flow: create → approve (buyer) → capture.

Usage:
    from goliath.integrations.paypal import PayPalClient

    pp = PayPalClient()

    # Create an order
    order = pp.create_order(amount="29.99", currency="USD")

    # Get order details
    details = pp.get_order(order_id="ORDER_ID")

    # Capture a payment (after buyer approval)
    capture = pp.capture_order(order_id="ORDER_ID")

    # Create a payout
    pp.create_payout(email="seller@example.com", amount="50.00", currency="USD")
"""

import requests

from goliath import config

_SANDBOX_BASE = "https://api-m.sandbox.paypal.com"
_LIVE_BASE = "https://api-m.paypal.com"


class PayPalClient:
    """PayPal REST API v2 client for orders, payments, and payouts."""

    def __init__(self):
        if not config.PAYPAL_CLIENT_ID or not config.PAYPAL_CLIENT_SECRET:
            raise RuntimeError(
                "PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET must be set. "
                "Add them to .env or export as environment variables. "
                "See integrations/paypal.py for setup instructions."
            )

        is_sandbox = config.PAYPAL_SANDBOX.lower() in ("true", "1", "yes", "")
        self._base = _SANDBOX_BASE if is_sandbox else _LIVE_BASE
        self._client_id = config.PAYPAL_CLIENT_ID
        self._client_secret = config.PAYPAL_CLIENT_SECRET

        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Get an OAuth 2.0 access token using client credentials."""
        resp = requests.post(
            f"{self._base}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._client_secret),
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    # -- Orders ------------------------------------------------------------

    def create_order(
        self,
        amount: str,
        currency: str = "USD",
        intent: str = "CAPTURE",
        description: str = "",
    ) -> dict:
        """Create an order.

        Args:
            amount:      Order amount as a string (e.g. "29.99").
            currency:    ISO 4217 currency code (e.g. "USD", "EUR").
            intent:      "CAPTURE" (immediate) or "AUTHORIZE" (auth only).
            description: Optional item description.

        Returns:
            Order resource dict with id and approval links.
        """
        purchase_unit: dict = {
            "amount": {"currency_code": currency, "value": amount},
        }
        if description:
            purchase_unit["description"] = description

        body = {
            "intent": intent,
            "purchase_units": [purchase_unit],
        }
        return self._post("/v2/checkout/orders", json=body)

    def get_order(self, order_id: str) -> dict:
        """Get order details.

        Args:
            order_id: PayPal order ID.

        Returns:
            Order resource dict.
        """
        return self._get(f"/v2/checkout/orders/{order_id}")

    def capture_order(self, order_id: str) -> dict:
        """Capture payment for an approved order.

        Args:
            order_id: PayPal order ID (must be in APPROVED status).

        Returns:
            Capture response dict.
        """
        return self._post(f"/v2/checkout/orders/{order_id}/capture")

    def authorize_order(self, order_id: str) -> dict:
        """Authorize payment for an approved order.

        Args:
            order_id: PayPal order ID.

        Returns:
            Authorization response dict.
        """
        return self._post(f"/v2/checkout/orders/{order_id}/authorize")

    # -- Payments ----------------------------------------------------------

    def capture_authorization(
        self, authorization_id: str, amount: str | None = None, currency: str = "USD"
    ) -> dict:
        """Capture a previously authorized payment.

        Args:
            authorization_id: Authorization ID.
            amount:           Optional amount (None = full authorized amount).
            currency:         Currency code.

        Returns:
            Capture resource dict.
        """
        body: dict = {}
        if amount is not None:
            body["amount"] = {"currency_code": currency, "value": amount}
        return self._post(
            f"/v2/payments/authorizations/{authorization_id}/capture", json=body
        )

    def refund_capture(
        self, capture_id: str, amount: str | None = None, currency: str = "USD"
    ) -> dict:
        """Refund a captured payment.

        Args:
            capture_id: Capture ID.
            amount:     Optional partial refund amount (None = full refund).
            currency:   Currency code.

        Returns:
            Refund resource dict.
        """
        body: dict = {}
        if amount is not None:
            body["amount"] = {"currency_code": currency, "value": amount}
        return self._post(f"/v2/payments/captures/{capture_id}/refund", json=body)

    # -- Payouts -----------------------------------------------------------

    def create_payout(
        self,
        email: str,
        amount: str,
        currency: str = "USD",
        note: str = "",
    ) -> dict:
        """Send a payout to an email address.

        Args:
            email:    Recipient email.
            amount:   Payout amount string (e.g. "50.00").
            currency: ISO currency code.
            note:     Optional note to recipient.

        Returns:
            Payout batch resource dict.
        """
        body = {
            "sender_batch_header": {
                "email_subject": "You have a payment",
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "receiver": email,
                    "amount": {"currency": currency, "value": amount},
                    "note": note,
                }
            ],
        }
        return self._post("/v1/payments/payouts", json=body)

    def get_payout(self, payout_batch_id: str) -> dict:
        """Get payout batch details.

        Args:
            payout_batch_id: Payout batch ID.

        Returns:
            Payout batch resource dict.
        """
        return self._get(f"/v1/payments/payouts/{payout_batch_id}")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
