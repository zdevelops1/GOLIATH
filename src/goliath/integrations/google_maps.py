"""
Google Maps Integration — geocoding, places, directions, and distance matrix via Google Maps Platform.

SETUP INSTRUCTIONS
==================

1. Go to https://console.cloud.google.com/ and create or select a project.

2. Enable the following APIs:
   - Geocoding API
   - Places API
   - Directions API
   - Distance Matrix API

3. Go to Credentials and create an API key.

4. Add to your .env:
     GOOGLE_MAPS_API_KEY=AIzaXxxxxxxxxxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Billing must be enabled on your Google Cloud project.
- Free tier: $200/month credit (covers ~28,000 geocoding requests).
- API docs: https://developers.google.com/maps/documentation
- All requests use the API key as a query parameter.
- Place IDs are stable identifiers; prefer them over addresses when possible.

Usage:
    from goliath.integrations.google_maps import GoogleMapsClient

    gm = GoogleMapsClient()

    # Geocode an address
    result = gm.geocode("1600 Amphitheatre Parkway, Mountain View, CA")

    # Reverse geocode coordinates
    result = gm.reverse_geocode(lat=37.4224764, lng=-122.0842499)

    # Search for nearby places
    places = gm.nearby_search(lat=40.7128, lng=-74.0060, radius=1000, keyword="coffee")

    # Text search for places
    places = gm.text_search("best pizza in New York")

    # Get place details
    details = gm.place_details("ChIJN1t_tDeuEmsRUsoyG83frY4")

    # Get directions
    route = gm.directions(origin="New York, NY", destination="Boston, MA")

    # Distance matrix
    matrix = gm.distance_matrix(
        origins=["New York, NY", "Philadelphia, PA"],
        destinations=["Boston, MA", "Washington, DC"],
    )
"""

import requests

from goliath import config

_API_BASE = "https://maps.googleapis.com/maps/api"


class GoogleMapsClient:
    """Google Maps Platform client for geocoding, places, and directions."""

    def __init__(self):
        if not config.GOOGLE_MAPS_API_KEY:
            raise RuntimeError(
                "GOOGLE_MAPS_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/google_maps.py for setup instructions."
            )

        self.api_key = config.GOOGLE_MAPS_API_KEY
        self.session = requests.Session()

    # -- Geocoding ---------------------------------------------------------

    def geocode(self, address: str) -> list[dict]:
        """Geocode an address to coordinates.

        Args:
            address: Street address or place name.

        Returns:
            List of result dicts with geometry, formatted_address, etc.
        """
        data = self._get(
            "/geocode/json",
            params={"address": address, "key": self.api_key},
        )
        return data.get("results", [])

    def reverse_geocode(self, lat: float, lng: float) -> list[dict]:
        """Reverse geocode coordinates to addresses.

        Args:
            lat: Latitude.
            lng: Longitude.

        Returns:
            List of address result dicts.
        """
        data = self._get(
            "/geocode/json",
            params={"latlng": f"{lat},{lng}", "key": self.api_key},
        )
        return data.get("results", [])

    # -- Places ------------------------------------------------------------

    def nearby_search(
        self,
        lat: float,
        lng: float,
        radius: int = 1500,
        keyword: str | None = None,
        type: str | None = None,
        page_token: str | None = None,
    ) -> dict:
        """Search for nearby places.

        Args:
            lat:        Latitude of center point.
            lng:        Longitude of center point.
            radius:     Search radius in meters (max 50000).
            keyword:    Keyword to filter results.
            type:       Place type (e.g. "restaurant", "cafe", "hospital").
            page_token: Token for next page of results.

        Returns:
            Dict with "results" list and optional "next_page_token".
        """
        params: dict = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": self.api_key,
        }
        if keyword:
            params["keyword"] = keyword
        if type:
            params["type"] = type
        if page_token:
            params["pagetoken"] = page_token
        return self._get("/place/nearbysearch/json", params=params)

    def text_search(self, query: str, page_token: str | None = None) -> dict:
        """Search places by text query.

        Args:
            query:      Search text (e.g. "best pizza in New York").
            page_token: Token for next page.

        Returns:
            Dict with "results" list.
        """
        params: dict = {"query": query, "key": self.api_key}
        if page_token:
            params["pagetoken"] = page_token
        return self._get("/place/textsearch/json", params=params)

    def place_details(self, place_id: str, fields: str | None = None) -> dict:
        """Get detailed information about a place.

        Args:
            place_id: Google Place ID.
            fields:   Comma-separated fields (e.g. "name,rating,formatted_phone_number").

        Returns:
            Place detail dict.
        """
        params: dict = {"place_id": place_id, "key": self.api_key}
        if fields:
            params["fields"] = fields
        data = self._get("/place/details/json", params=params)
        return data.get("result", {})

    def autocomplete(self, input_text: str, types: str | None = None) -> list[dict]:
        """Get place autocomplete predictions.

        Args:
            input_text: Partial search text.
            types:      Type filter (e.g. "geocode", "establishment", "(cities)").

        Returns:
            List of prediction dicts.
        """
        params: dict = {"input": input_text, "key": self.api_key}
        if types:
            params["types"] = types
        data = self._get("/place/autocomplete/json", params=params)
        return data.get("predictions", [])

    # -- Directions --------------------------------------------------------

    def directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        waypoints: list[str] | None = None,
        alternatives: bool = False,
    ) -> list[dict]:
        """Get directions between locations.

        Args:
            origin:       Starting address or place.
            destination:  Ending address or place.
            mode:         Travel mode ("driving", "walking", "bicycling", "transit").
            waypoints:    Optional intermediate stops.
            alternatives: Return alternative routes.

        Returns:
            List of route dicts with legs, steps, distance, duration.
        """
        params: dict = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "alternatives": str(alternatives).lower(),
            "key": self.api_key,
        }
        if waypoints:
            params["waypoints"] = "|".join(waypoints)
        data = self._get("/directions/json", params=params)
        return data.get("routes", [])

    # -- Distance Matrix ---------------------------------------------------

    def distance_matrix(
        self,
        origins: list[str],
        destinations: list[str],
        mode: str = "driving",
    ) -> dict:
        """Calculate distance and time between multiple origins and destinations.

        Args:
            origins:      List of origin addresses.
            destinations: List of destination addresses.
            mode:         Travel mode.

        Returns:
            Matrix dict with rows of elements containing distance and duration.
        """
        return self._get(
            "/distancematrix/json",
            params={
                "origins": "|".join(origins),
                "destinations": "|".join(destinations),
                "mode": mode,
                "key": self.api_key,
            },
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
