"""
Stripe Integration — manage payments, customers, and subscriptions via the Stripe API.

SETUP INSTRUCTIONS
==================

1. Create a Stripe account at https://stripe.com (or log in).

2. Go to https://dashboard.stripe.com/apikeys

3. Copy your Secret Key:
   - Test mode: starts with "sk_test_"
   - Live mode: starts with "sk_live_"

4. Add to your .env:
     STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Use test-mode keys (sk_test_) during development — no real charges.
- Stripe uses API versioning via headers. This client uses your account's
  default version.
- All monetary amounts are in the smallest currency unit (e.g. cents for USD:
  $10.00 = 1000).
- Rate limit: 100 read requests/second, 100 write requests/second.

Usage:
    from goliath.integrations.stripe import StripeClient

    stripe = StripeClient()

    # Create a customer
    customer = stripe.create_customer(email="user@example.com", name="Jane Doe")

    # Create a one-time payment intent
    intent = stripe.create_payment_intent(amount=2000, currency="usd")

    # List recent charges
    charges = stripe.list_charges(limit=10)

    # Create a product and price
    product = stripe.create_product(name="Pro Plan")
    price = stripe.create_price(product_id=product["id"], unit_amount=999, currency="usd", recurring_interval="month")
"""

import requests

from goliath import config

_API_BASE = "https://api.stripe.com/v1"


class StripeClient:
    """Stripe API client for payments, customers, and subscriptions."""

    def __init__(self):
        if not config.STRIPE_SECRET_KEY:
            raise RuntimeError(
                "STRIPE_SECRET_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/stripe.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.auth = (config.STRIPE_SECRET_KEY, "")

    # -- Customers ---------------------------------------------------------

    def create_customer(
        self,
        email: str | None = None,
        name: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a new customer.

        Args:
            email:  Customer email.
            name:   Customer name.
            kwargs: Additional fields (phone, description, metadata, etc.).

        Returns:
            Stripe customer object.
        """
        data: dict = {**kwargs}
        if email:
            data["email"] = email
        if name:
            data["name"] = name
        return self._post("/customers", data=data)

    def get_customer(self, customer_id: str) -> dict:
        """Retrieve a customer by ID.

        Args:
            customer_id: Stripe customer ID (e.g. "cus_xxx").

        Returns:
            Stripe customer object.
        """
        return self._get(f"/customers/{customer_id}")

    def list_customers(self, limit: int = 10, **kwargs) -> list[dict]:
        """List customers.

        Args:
            limit:  Number of customers (1–100).
            kwargs: Additional filters (email, created, etc.).

        Returns:
            List of customer objects.
        """
        kwargs["limit"] = limit
        return self._get("/customers", params=kwargs).get("data", [])

    # -- Payment Intents ---------------------------------------------------

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a payment intent.

        Args:
            amount:      Amount in smallest currency unit (e.g. 2000 = $20.00).
            currency:    Three-letter ISO currency code.
            customer_id: Optional Stripe customer ID.
            kwargs:      Additional fields (payment_method_types, metadata, etc.).

        Returns:
            Stripe PaymentIntent object.
        """
        data: dict = {"amount": amount, "currency": currency, **kwargs}
        if customer_id:
            data["customer"] = customer_id
        return self._post("/payment_intents", data=data)

    def get_payment_intent(self, intent_id: str) -> dict:
        """Retrieve a payment intent.

        Args:
            intent_id: Stripe PaymentIntent ID (e.g. "pi_xxx").

        Returns:
            PaymentIntent object.
        """
        return self._get(f"/payment_intents/{intent_id}")

    # -- Charges -----------------------------------------------------------

    def list_charges(self, limit: int = 10, **kwargs) -> list[dict]:
        """List recent charges.

        Args:
            limit:  Number of charges (1–100).
            kwargs: Additional filters (customer, created, etc.).

        Returns:
            List of charge objects.
        """
        kwargs["limit"] = limit
        return self._get("/charges", params=kwargs).get("data", [])

    # -- Products & Prices -------------------------------------------------

    def create_product(self, name: str, **kwargs) -> dict:
        """Create a product.

        Args:
            name:   Product name.
            kwargs: Additional fields (description, images, metadata, etc.).

        Returns:
            Stripe product object.
        """
        return self._post("/products", data={"name": name, **kwargs})

    def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str = "usd",
        recurring_interval: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a price for a product.

        Args:
            product_id:         Stripe product ID.
            unit_amount:        Price in smallest currency unit.
            currency:           Three-letter ISO currency code.
            recurring_interval: "day", "week", "month", or "year" for subscriptions.
                                None for one-time prices.
            kwargs:             Additional fields.

        Returns:
            Stripe price object.
        """
        data: dict = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
            **kwargs,
        }
        if recurring_interval:
            data["recurring[interval]"] = recurring_interval
        return self._post("/prices", data=data)

    def list_prices(self, product_id: str | None = None, limit: int = 10) -> list[dict]:
        """List prices, optionally filtered by product.

        Args:
            product_id: Filter by Stripe product ID.
            limit:      Number of prices (1–100).

        Returns:
            List of price objects.
        """
        params: dict = {"limit": limit}
        if product_id:
            params["product"] = product_id
        return self._get("/prices", params=params).get("data", [])

    # -- Subscriptions -----------------------------------------------------

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        **kwargs,
    ) -> dict:
        """Create a subscription.

        Args:
            customer_id: Stripe customer ID.
            price_id:    Stripe price ID.
            kwargs:      Additional fields (trial_period_days, metadata, etc.).

        Returns:
            Stripe subscription object.
        """
        data: dict = {
            "customer": customer_id,
            "items[0][price]": price_id,
            **kwargs,
        }
        return self._post("/subscriptions", data=data)

    def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription immediately.

        Args:
            subscription_id: Stripe subscription ID (e.g. "sub_xxx").

        Returns:
            Cancelled subscription object.
        """
        return self._delete(f"/subscriptions/{subscription_id}")

    # -- Refunds -----------------------------------------------------------

    def create_refund(
        self,
        charge_id: str | None = None,
        payment_intent_id: str | None = None,
        amount: int | None = None,
    ) -> dict:
        """Create a refund.

        Args:
            charge_id:         Stripe charge ID to refund.
            payment_intent_id: Or PaymentIntent ID to refund.
            amount:            Partial refund amount (None = full refund).

        Returns:
            Stripe refund object.
        """
        data: dict = {}
        if charge_id:
            data["charge"] = charge_id
        if payment_intent_id:
            data["payment_intent"] = payment_intent_id
        if amount is not None:
            data["amount"] = amount
        return self._post("/refunds", data=data)

    # -- Balance -----------------------------------------------------------

    def get_balance(self) -> dict:
        """Get the current account balance.

        Returns:
            Stripe balance object with available and pending amounts.
        """
        return self._get("/balance")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict:
        resp = self.session.delete(f"{_API_BASE}{path}")
        resp.raise_for_status()
        return resp.json()
