"""
Yelp Integration — search businesses, read reviews, and get local data via the Yelp Fusion API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.yelp.com/developers and sign up or log in.

2. Create an app at https://www.yelp.com/developers/v3/manage_app

3. Copy your API Key.

4. Add to your .env:
     YELP_API_KEY=your_api_key_here

IMPORTANT NOTES
===============
- Free tier: 500 API calls/day.
- API docs: https://docs.developer.yelp.com/docs/fusion-intro
- Returns business details, reviews, photos, and search results.
- Supports filtering by location, category, price, and more.
- Review data is limited to 3 reviews per business on the free tier.

Usage:
    from goliath.integrations.yelp import YelpClient

    y = YelpClient()

    # Search businesses
    results = y.search("coffee", location="San Francisco, CA")

    # Search by coordinates
    results = y.search("pizza", latitude=40.7128, longitude=-74.0060)

    # Get business details
    biz = y.get_business("north-india-restaurant-san-francisco")

    # Get reviews
    reviews = y.get_reviews("north-india-restaurant-san-francisco")

    # Search by phone number
    biz = y.phone_search("+14155551234")

    # Autocomplete
    suggestions = y.autocomplete("sush", latitude=37.7749, longitude=-122.4194)
"""

import requests

from goliath import config

_API_BASE = "https://api.yelp.com/v3"


class YelpClient:
    """Yelp Fusion API client for business search, reviews, and local data."""

    def __init__(self):
        if not config.YELP_API_KEY:
            raise RuntimeError(
                "YELP_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/yelp.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.YELP_API_KEY}",
            "Accept": "application/json",
        })

    # -- Business Search ---------------------------------------------------

    def search(
        self,
        term: str,
        location: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        radius: int | None = None,
        categories: str | None = None,
        price: str | None = None,
        sort_by: str = "best_match",
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Search for businesses.

        Args:
            term:       Search term (e.g. "coffee", "restaurants").
            location:   Address or area (e.g. "San Francisco, CA"). Required if no lat/lon.
            latitude:   Latitude (alternative to location).
            longitude:  Longitude (alternative to location).
            radius:     Search radius in meters (max 40000).
            categories: Comma-separated category aliases (e.g. "bars,french").
            price:      Price filter ("1", "2", "3", "4" or comma-separated "1,2").
            sort_by:    "best_match", "rating", "review_count", or "distance".
            limit:      Number of results (max 50).
            offset:     Pagination offset.

        Returns:
            Dict with "businesses" list, "total", and "region".
        """
        params: dict = {
            "term": term,
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset,
        }
        if location:
            params["location"] = location
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude
        if radius:
            params["radius"] = radius
        if categories:
            params["categories"] = categories
        if price:
            params["price"] = price
        return self._get("/businesses/search", params=params)

    # -- Business Details --------------------------------------------------

    def get_business(self, business_id: str) -> dict:
        """Get detailed information about a business.

        Args:
            business_id: Business ID or alias (e.g. "north-india-restaurant-san-francisco").

        Returns:
            Business dict with name, rating, hours, photos, etc.
        """
        return self._get(f"/businesses/{business_id}")

    # -- Reviews -----------------------------------------------------------

    def get_reviews(self, business_id: str, sort_by: str = "yelp_sort") -> list[dict]:
        """Get reviews for a business.

        Args:
            business_id: Business ID or alias.
            sort_by:     "yelp_sort" or "newest".

        Returns:
            List of review dicts.
        """
        data = self._get(
            f"/businesses/{business_id}/reviews",
            params={"sort_by": sort_by},
        )
        return data.get("reviews", [])

    # -- Phone Search ------------------------------------------------------

    def phone_search(self, phone: str) -> list[dict]:
        """Search businesses by phone number.

        Args:
            phone: Phone number in E.164 format (e.g. "+14155551234").

        Returns:
            List of matching business dicts.
        """
        data = self._get("/businesses/search/phone", params={"phone": phone})
        return data.get("businesses", [])

    # -- Autocomplete ------------------------------------------------------

    def autocomplete(
        self,
        text: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        """Get autocomplete suggestions.

        Args:
            text:      Partial search text.
            latitude:  Optional latitude for location context.
            longitude: Optional longitude for location context.

        Returns:
            Dict with "terms", "businesses", and "categories" suggestions.
        """
        params: dict = {"text": text}
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude
        return self._get("/autocomplete", params=params)

    # -- Categories --------------------------------------------------------

    def get_categories(self, locale: str = "en_US") -> list[dict]:
        """Get all available business categories.

        Args:
            locale: Locale code (e.g. "en_US").

        Returns:
            List of category dicts with alias and title.
        """
        data = self._get("/categories", params={"locale": locale})
        return data.get("categories", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
