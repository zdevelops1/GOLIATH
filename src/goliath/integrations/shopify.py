"""
Shopify Integration — manage products, orders, and customers via the Shopify Admin API.

SETUP INSTRUCTIONS
==================

1. Log in to your Shopify admin at https://your-store.myshopify.com/admin

2. Go to Settings > Apps and sales channels > Develop apps.

3. Click "Create an app" and give it a name (e.g. "GOLIATH").

4. Under "Configuration", select the Admin API scopes you need:
   - read_products, write_products
   - read_orders, write_orders
   - read_customers, write_customers
   - read_inventory, write_inventory

5. Click "Install app" and copy the Admin API access token.

6. Add to your .env:
     SHOPIFY_STORE=your-store.myshopify.com
     SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- The access token starts with "shpat_" for custom apps.
- API version is pinned to 2024-10. Update _API_VERSION for newer versions.
- Rate limit: 40 requests/second (bucket with leaky bucket algorithm).
- All monetary values are strings (e.g. "19.99") to avoid float precision issues.

Usage:
    from goliath.integrations.shopify import ShopifyClient

    shop = ShopifyClient()

    # List products
    products = shop.list_products(limit=10)

    # Create a product
    shop.create_product(title="T-Shirt", body_html="<p>Cool shirt</p>", vendor="GOLIATH")

    # Get an order
    order = shop.get_order(order_id=123456)

    # List customers
    customers = shop.list_customers(limit=5)
"""

import requests

from goliath import config

_API_VERSION = "2024-10"


class ShopifyClient:
    """Shopify Admin API client for products, orders, and customers."""

    def __init__(self):
        if not config.SHOPIFY_ACCESS_TOKEN:
            raise RuntimeError(
                "SHOPIFY_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/shopify.py for setup instructions."
            )
        if not config.SHOPIFY_STORE:
            raise RuntimeError(
                "SHOPIFY_STORE is not set (e.g. 'your-store.myshopify.com'). "
                "Add it to .env or export as an environment variable."
            )

        self._store = config.SHOPIFY_STORE.rstrip("/")
        self._base = f"https://{self._store}/admin/api/{_API_VERSION}"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Shopify-Access-Token": config.SHOPIFY_ACCESS_TOKEN,
                "Content-Type": "application/json",
            }
        )

    # -- Products ----------------------------------------------------------

    def list_products(self, limit: int = 50, **params) -> list[dict]:
        """List products in the store.

        Args:
            limit:  Number of products (1–250).
            params: Additional query params (e.g. collection_id, status).

        Returns:
            List of product dicts.
        """
        params["limit"] = limit
        return self._get("/products.json", params=params).get("products", [])

    def get_product(self, product_id: int) -> dict:
        """Get a single product by ID.

        Args:
            product_id: Shopify product ID.

        Returns:
            Product dict.
        """
        return self._get(f"/products/{product_id}.json").get("product", {})

    def create_product(self, title: str, **kwargs) -> dict:
        """Create a new product.

        Args:
            title:  Product title.
            kwargs: Additional fields — body_html, vendor, product_type,
                    tags, variants, images, etc.

        Returns:
            Created product dict.
        """
        product = {"title": title, **kwargs}
        return self._post("/products.json", json={"product": product}).get(
            "product", {}
        )

    def update_product(self, product_id: int, **kwargs) -> dict:
        """Update a product.

        Args:
            product_id: Shopify product ID.
            kwargs:     Fields to update (title, body_html, etc.).

        Returns:
            Updated product dict.
        """
        product = {"id": product_id, **kwargs}
        return self._put(f"/products/{product_id}.json", json={"product": product}).get(
            "product", {}
        )

    def delete_product(self, product_id: int) -> None:
        """Delete a product.

        Args:
            product_id: Shopify product ID.
        """
        resp = self.session.delete(f"{self._base}/products/{product_id}.json")
        resp.raise_for_status()

    # -- Orders ------------------------------------------------------------

    def list_orders(self, limit: int = 50, status: str = "any", **params) -> list[dict]:
        """List orders.

        Args:
            limit:  Number of orders (1–250).
            status: "open", "closed", "cancelled", or "any".
            params: Additional query params (e.g. created_at_min).

        Returns:
            List of order dicts.
        """
        params.update({"limit": limit, "status": status})
        return self._get("/orders.json", params=params).get("orders", [])

    def get_order(self, order_id: int) -> dict:
        """Get a single order by ID.

        Args:
            order_id: Shopify order ID.

        Returns:
            Order dict.
        """
        return self._get(f"/orders/{order_id}.json").get("order", {})

    def close_order(self, order_id: int) -> dict:
        """Close an order.

        Args:
            order_id: Shopify order ID.

        Returns:
            Closed order dict.
        """
        return self._post(f"/orders/{order_id}/close.json").get("order", {})

    def cancel_order(self, order_id: int, reason: str = "other") -> dict:
        """Cancel an order.

        Args:
            order_id: Shopify order ID.
            reason:   Cancellation reason — "customer", "fraud", "inventory", "declined", "other".

        Returns:
            Cancelled order dict.
        """
        return self._post(
            f"/orders/{order_id}/cancel.json", json={"reason": reason}
        ).get("order", {})

    # -- Customers ---------------------------------------------------------

    def list_customers(self, limit: int = 50, **params) -> list[dict]:
        """List customers.

        Args:
            limit:  Number of customers (1–250).
            params: Additional query params.

        Returns:
            List of customer dicts.
        """
        params["limit"] = limit
        return self._get("/customers.json", params=params).get("customers", [])

    def get_customer(self, customer_id: int) -> dict:
        """Get a single customer by ID.

        Args:
            customer_id: Shopify customer ID.

        Returns:
            Customer dict.
        """
        return self._get(f"/customers/{customer_id}.json").get("customer", {})

    def search_customers(self, query: str, limit: int = 50) -> list[dict]:
        """Search customers by query string.

        Args:
            query: Search query (e.g. email, name).
            limit: Number of results.

        Returns:
            List of matching customer dicts.
        """
        return self._get(
            "/customers/search.json", params={"query": query, "limit": limit}
        ).get("customers", [])

    # -- Inventory ---------------------------------------------------------

    def get_inventory_levels(self, location_id: int, **params) -> list[dict]:
        """Get inventory levels for a location.

        Args:
            location_id: Shopify location ID.
            params:      Additional query params.

        Returns:
            List of inventory level dicts.
        """
        params["location_ids"] = location_id
        return self._get("/inventory_levels.json", params=params).get(
            "inventory_levels", []
        )

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

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
