"""Tests for new integrations: YouTube, LinkedIn, Shopify, Stripe, Twilio."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------


class TestYouTubeClient:
    @patch("goliath.integrations.youtube.config")
    def test_no_credentials_raises(self, mock_config):
        mock_config.YOUTUBE_API_KEY = ""
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        from goliath.integrations.youtube import YouTubeClient

        with pytest.raises(RuntimeError, match="Neither YOUTUBE_API_KEY"):
            YouTubeClient()

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_api_key_only_init(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        assert client._api_key == "test-key"
        assert client._token == ""

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"id": "vid1"}, {"id": "vid2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        results = client.search("Python tutorial", max_results=2)

        assert len(results) == 2
        call_args = client.session.get.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert params["q"] == "Python tutorial"
        assert params["maxResults"] == 2

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_api_key_passed_in_params(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "my-api-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        client.search("test")

        call_args = client.session.get.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert params["key"] == "my-api-key"

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_get_video_not_found(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(ValueError, match="Video not found"):
            client.get_video("nonexistent")

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_upload_requires_token(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(RuntimeError, match="YOUTUBE_ACCESS_TOKEN is required"):
            client.upload("video.mp4", title="Test")

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_upload_file_not_found(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = ""
        mock_config.YOUTUBE_ACCESS_TOKEN = "token"

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(FileNotFoundError):
            client.upload("/nonexistent/video.mp4", title="Test")

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_update_no_fields_raises(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = ""
        mock_config.YOUTUBE_ACCESS_TOKEN = "token"

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(ValueError, match="No fields to update"):
            client.update_video("vid1")

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_delete_requires_token(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(RuntimeError, match="YOUTUBE_ACCESS_TOKEN is required"):
            client.delete_video("vid1")

    @patch("goliath.integrations.youtube.requests")
    @patch("goliath.integrations.youtube.config")
    def test_get_channel_not_found(self, mock_config, mock_requests):
        mock_config.YOUTUBE_API_KEY = "test-key"
        mock_config.YOUTUBE_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.youtube import YouTubeClient

        client = YouTubeClient()
        with pytest.raises(ValueError, match="Channel not found"):
            client.get_channel("nonexistent")


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------


class TestLinkedInClient:
    @patch("goliath.integrations.linkedin.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.LINKEDIN_ACCESS_TOKEN = ""
        mock_config.LINKEDIN_PERSON_ID = "pid"

        from goliath.integrations.linkedin import LinkedInClient

        with pytest.raises(RuntimeError, match="LINKEDIN_ACCESS_TOKEN"):
            LinkedInClient()

    @patch("goliath.integrations.linkedin.config")
    def test_missing_person_id_raises(self, mock_config):
        mock_config.LINKEDIN_ACCESS_TOKEN = "token"
        mock_config.LINKEDIN_PERSON_ID = ""

        from goliath.integrations.linkedin import LinkedInClient

        with pytest.raises(RuntimeError, match="LINKEDIN_PERSON_ID"):
            LinkedInClient()

    @patch("goliath.integrations.linkedin.requests")
    @patch("goliath.integrations.linkedin.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.LINKEDIN_ACCESS_TOKEN = "tok123"
        mock_config.LINKEDIN_PERSON_ID = "pid"

        from goliath.integrations.linkedin import LinkedInClient

        client = LinkedInClient()
        headers = client.session.headers
        headers.update.assert_called_once()
        call_kwargs = headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer tok123"
        assert "X-Restli-Protocol-Version" in call_kwargs
        assert "LinkedIn-Version" in call_kwargs

    @patch("goliath.integrations.linkedin.requests")
    @patch("goliath.integrations.linkedin.config")
    def test_create_text_post(self, mock_config, mock_requests):
        mock_config.LINKEDIN_ACCESS_TOKEN = "tok"
        mock_config.LINKEDIN_PERSON_ID = "person123"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "urn:li:share:1"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.linkedin import LinkedInClient

        client = LinkedInClient()
        client.create_post("Hello LinkedIn!")

        call_args = client.session.post.call_args
        payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
        assert payload["author"] == "urn:li:person:person123"
        share = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
        assert share["shareCommentary"]["text"] == "Hello LinkedIn!"
        assert share["shareMediaCategory"] == "NONE"

    @patch("goliath.integrations.linkedin.requests")
    @patch("goliath.integrations.linkedin.config")
    def test_create_link_post(self, mock_config, mock_requests):
        mock_config.LINKEDIN_ACCESS_TOKEN = "tok"
        mock_config.LINKEDIN_PERSON_ID = "person123"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "urn:li:share:2"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.linkedin import LinkedInClient

        client = LinkedInClient()
        client.create_post("Check this out", link_url="https://example.com")

        call_args = client.session.post.call_args
        payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
        share = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
        assert share["shareMediaCategory"] == "ARTICLE"
        assert share["media"][0]["originalUrl"] == "https://example.com"

    @patch("goliath.integrations.linkedin.requests")
    @patch("goliath.integrations.linkedin.config")
    def test_image_post_file_not_found(self, mock_config, mock_requests):
        mock_config.LINKEDIN_ACCESS_TOKEN = "tok"
        mock_config.LINKEDIN_PERSON_ID = "pid"

        from goliath.integrations.linkedin import LinkedInClient

        client = LinkedInClient()
        with pytest.raises(FileNotFoundError):
            client.create_image_post("Look!", "/nonexistent/photo.jpg")

    @patch("goliath.integrations.linkedin.requests")
    @patch("goliath.integrations.linkedin.config")
    def test_delete_post_encodes_urn(self, mock_config, mock_requests):
        mock_config.LINKEDIN_ACCESS_TOKEN = "tok"
        mock_config.LINKEDIN_PERSON_ID = "pid"

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.linkedin import LinkedInClient

        client = LinkedInClient()
        client.delete_post("urn:li:share:123")

        url = client.session.delete.call_args[0][0]
        assert "urn%3Ali%3Ashare%3A123" in url


# ---------------------------------------------------------------------------
# Shopify
# ---------------------------------------------------------------------------


class TestShopifyClient:
    @patch("goliath.integrations.shopify.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.SHOPIFY_ACCESS_TOKEN = ""
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        from goliath.integrations.shopify import ShopifyClient

        with pytest.raises(RuntimeError, match="SHOPIFY_ACCESS_TOKEN"):
            ShopifyClient()

    @patch("goliath.integrations.shopify.config")
    def test_missing_store_raises(self, mock_config):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_xxx"
        mock_config.SHOPIFY_STORE = ""

        from goliath.integrations.shopify import ShopifyClient

        with pytest.raises(RuntimeError, match="SHOPIFY_STORE"):
            ShopifyClient()

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-Shopify-Access-Token"] == "shpat_test"

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_list_products(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"products": [{"id": 1, "title": "Shirt"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        products = client.list_products(limit=10)

        assert len(products) == 1
        assert products[0]["title"] == "Shirt"
        url = client.session.get.call_args[0][0]
        assert "/products.json" in url
        assert "2024-10" in url

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_create_product(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"product": {"id": 2, "title": "Hat"}}
        mock_resp.status_code = 201
        mock_resp.content = b'{"product": {}}'
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        client.create_product(title="Hat", vendor="GOLIATH")

        payload = client.session.post.call_args.kwargs["json"]
        assert payload["product"]["title"] == "Hat"
        assert payload["product"]["vendor"] == "GOLIATH"

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_list_orders(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"orders": [{"id": 100, "total_price": "29.99"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        orders = client.list_orders(limit=5, status="open")

        assert len(orders) == 1
        call_args = client.session.get.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert params["status"] == "open"

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_search_customers(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "customers": [{"id": 1, "email": "user@example.com"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        results = client.search_customers("user@example.com")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/customers/search.json" in url

    @patch("goliath.integrations.shopify.requests")
    @patch("goliath.integrations.shopify.config")
    def test_cancel_order(self, mock_config, mock_requests):
        mock_config.SHOPIFY_ACCESS_TOKEN = "shpat_test"
        mock_config.SHOPIFY_STORE = "test.myshopify.com"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "order": {"id": 100, "cancelled_at": "2025-01-01"}
        }
        mock_resp.status_code = 200
        mock_resp.content = b'{"order": {}}'
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.shopify import ShopifyClient

        client = ShopifyClient()
        client.cancel_order(100, reason="fraud")

        url = client.session.post.call_args[0][0]
        assert "/orders/100/cancel.json" in url
        payload = client.session.post.call_args.kwargs["json"]
        assert payload["reason"] == "fraud"


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------


class TestStripeClient:
    @patch("goliath.integrations.stripe.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.STRIPE_SECRET_KEY = ""

        from goliath.integrations.stripe import StripeClient

        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY"):
            StripeClient()

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_auth_set(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        assert client.session.auth == ("sk_test_abc", "")

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_customer(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "cus_123", "email": "user@test.com"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_customer(email="user@test.com", name="Jane")

        call_args = client.session.post.call_args
        url = call_args[0][0]
        assert "/customers" in url
        data = call_args.kwargs.get("data", call_args[1].get("data", {}))
        assert data["email"] == "user@test.com"
        assert data["name"] == "Jane"

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_payment_intent(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "pi_123", "amount": 2000}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_payment_intent(amount=2000, currency="usd", customer_id="cus_1")

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["amount"] == 2000
        assert data["currency"] == "usd"
        assert data["customer"] == "cus_1"

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_product(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "prod_123", "name": "Pro Plan"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_product(name="Pro Plan")

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["name"] == "Pro Plan"

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_price_with_recurring(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "price_123"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_price(
            product_id="prod_1",
            unit_amount=999,
            currency="usd",
            recurring_interval="month",
        )

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["product"] == "prod_1"
        assert data["unit_amount"] == 999
        assert data["recurring[interval]"] == "month"

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_subscription(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "sub_123"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_subscription(customer_id="cus_1", price_id="price_1")

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["customer"] == "cus_1"
        assert data["items[0][price]"] == "price_1"

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_create_refund(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "re_123", "amount": 500}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.create_refund(charge_id="ch_1", amount=500)

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["charge"] == "ch_1"
        assert data["amount"] == 500

    @patch("goliath.integrations.stripe.requests")
    @patch("goliath.integrations.stripe.config")
    def test_cancel_subscription(self, mock_config, mock_requests):
        mock_config.STRIPE_SECRET_KEY = "sk_test_abc"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "sub_1", "status": "canceled"}
        mock_requests.Session.return_value.delete.return_value = mock_resp

        from goliath.integrations.stripe import StripeClient

        client = StripeClient()
        client.cancel_subscription("sub_1")

        url = client.session.delete.call_args[0][0]
        assert "/subscriptions/sub_1" in url


# ---------------------------------------------------------------------------
# Twilio
# ---------------------------------------------------------------------------


class TestTwilioClient:
    @patch("goliath.integrations.twilio.config")
    def test_missing_credentials_raises(self, mock_config):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = ""
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        from goliath.integrations.twilio import TwilioClient

        with pytest.raises(RuntimeError, match="Missing Twilio credentials"):
            TwilioClient()

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_auth_set(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        assert client.session.auth == ("AC123", "authtoken")

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_send_sms(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"sid": "SM123", "status": "queued"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        client.send(to="+15559876543", body="Hello!")

        call_args = client.session.post.call_args
        url = call_args[0][0]
        assert "/Messages.json" in url
        assert "AC123" in url
        data = call_args.kwargs.get("data", call_args[1].get("data", {}))
        assert data["To"] == "+15559876543"
        assert data["From"] == "+15551234567"
        assert data["Body"] == "Hello!"

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_send_mms_with_media(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"sid": "MM123", "status": "queued"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        client.send(
            to="+15559876543",
            body="Check this out!",
            media_url="https://example.com/photo.jpg",
        )

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["MediaUrl"] == "https://example.com/photo.jpg"

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_send_custom_from_number(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"sid": "SM456"}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        client.send(to="+15559876543", body="Hi", from_number="+15550001111")

        data = client.session.post.call_args.kwargs.get(
            "data", client.session.post.call_args[1].get("data", {})
        )
        assert data["From"] == "+15550001111"

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_get_message(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"sid": "SM123", "status": "delivered"}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        msg = client.get_message("SM123")

        assert msg["status"] == "delivered"
        url = client.session.get.call_args[0][0]
        assert "/Messages/SM123.json" in url

    @patch("goliath.integrations.twilio.requests")
    @patch("goliath.integrations.twilio.config")
    def test_list_messages(self, mock_config, mock_requests):
        mock_config.TWILIO_ACCOUNT_SID = "AC123"
        mock_config.TWILIO_AUTH_TOKEN = "authtoken"
        mock_config.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"sid": "SM1"}, {"sid": "SM2"}]}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.twilio import TwilioClient

        client = TwilioClient()
        messages = client.list_messages(limit=5)

        assert len(messages) == 2
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["PageSize"] == 5
