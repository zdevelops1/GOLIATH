"""
Weather API Integration — get current weather, forecasts, and historical data via OpenWeatherMap.

SETUP INSTRUCTIONS
==================

1. Go to https://openweathermap.org/ and create a free account.

2. Go to API keys (https://home.openweathermap.org/api_keys).

3. Copy your default key or generate a new one.

4. Add to your .env:
     OPENWEATHER_API_KEY=your_api_key_here

IMPORTANT NOTES
===============
- Free tier: 1000 API calls/day, current weather + 5-day forecast.
- API docs: https://openweathermap.org/api
- Supports units: "metric" (Celsius), "imperial" (Fahrenheit), "standard" (Kelvin).
- Location can be specified by city name, coordinates, or zip code.
- New API keys can take a few hours to activate.

Usage:
    from goliath.integrations.weather import WeatherClient

    w = WeatherClient()

    # Current weather by city
    current = w.get_current("London")

    # Current weather by coordinates
    current = w.get_current_by_coords(lat=51.5074, lon=-0.1278)

    # 5-day forecast
    forecast = w.get_forecast("New York", units="imperial")

    # Current weather by zip code
    current = w.get_current_by_zip("10001", country="US")

    # Air quality
    aqi = w.get_air_quality(lat=40.7128, lon=-74.0060)

    # Geocode a city name to coordinates
    coords = w.geocode("Tokyo")
"""

import requests

from goliath import config

_API_BASE = "https://api.openweathermap.org"


class WeatherClient:
    """OpenWeatherMap API client for weather data and forecasts."""

    def __init__(self):
        if not config.OPENWEATHER_API_KEY:
            raise RuntimeError(
                "OPENWEATHER_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/weather.py for setup instructions."
            )

        self.api_key = config.OPENWEATHER_API_KEY
        self.session = requests.Session()

    # -- Current Weather ---------------------------------------------------

    def get_current(self, city: str, units: str = "metric") -> dict:
        """Get current weather for a city.

        Args:
            city:  City name (e.g. "London", "New York,US").
            units: "metric", "imperial", or "standard".

        Returns:
            Weather dict with temp, humidity, wind, description, etc.
        """
        return self._get(
            "/data/2.5/weather",
            params={"q": city, "units": units, "appid": self.api_key},
        )

    def get_current_by_coords(
        self, lat: float, lon: float, units: str = "metric"
    ) -> dict:
        """Get current weather by coordinates.

        Args:
            lat:   Latitude.
            lon:   Longitude.
            units: "metric", "imperial", or "standard".

        Returns:
            Weather dict.
        """
        return self._get(
            "/data/2.5/weather",
            params={"lat": lat, "lon": lon, "units": units, "appid": self.api_key},
        )

    def get_current_by_zip(
        self, zip_code: str, country: str = "US", units: str = "metric"
    ) -> dict:
        """Get current weather by zip code.

        Args:
            zip_code: Zip/postal code.
            country:  ISO country code.
            units:    "metric", "imperial", or "standard".

        Returns:
            Weather dict.
        """
        return self._get(
            "/data/2.5/weather",
            params={
                "zip": f"{zip_code},{country}",
                "units": units,
                "appid": self.api_key,
            },
        )

    # -- Forecast ----------------------------------------------------------

    def get_forecast(
        self, city: str, units: str = "metric", cnt: int | None = None
    ) -> dict:
        """Get a 5-day / 3-hour forecast.

        Args:
            city:  City name.
            units: "metric", "imperial", or "standard".
            cnt:   Number of 3-hour periods to return (max 40).

        Returns:
            Forecast dict with "list" of forecast entries.
        """
        params: dict = {"q": city, "units": units, "appid": self.api_key}
        if cnt:
            params["cnt"] = cnt
        return self._get("/data/2.5/forecast", params=params)

    def get_forecast_by_coords(
        self, lat: float, lon: float, units: str = "metric"
    ) -> dict:
        """Get a 5-day forecast by coordinates.

        Args:
            lat:   Latitude.
            lon:   Longitude.
            units: "metric", "imperial", or "standard".

        Returns:
            Forecast dict.
        """
        return self._get(
            "/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "units": units, "appid": self.api_key},
        )

    # -- Air Quality -------------------------------------------------------

    def get_air_quality(self, lat: float, lon: float) -> dict:
        """Get current air quality index.

        Args:
            lat: Latitude.
            lon: Longitude.

        Returns:
            Air quality dict with AQI and component concentrations.
        """
        return self._get(
            "/data/2.5/air_pollution",
            params={"lat": lat, "lon": lon, "appid": self.api_key},
        )

    # -- Geocoding ---------------------------------------------------------

    def geocode(self, city: str, limit: int = 5) -> list[dict]:
        """Geocode a city name to coordinates.

        Args:
            city:  City name (optionally with state and country: "London,GB").
            limit: Max results.

        Returns:
            List of location dicts with lat, lon, country, state.
        """
        return self._get(
            "/geo/1.0/direct",
            params={"q": city, "limit": limit, "appid": self.api_key},
            is_list=True,
        )

    def reverse_geocode(self, lat: float, lon: float, limit: int = 5) -> list[dict]:
        """Reverse geocode coordinates to location names.

        Args:
            lat:   Latitude.
            lon:   Longitude.
            limit: Max results.

        Returns:
            List of location dicts.
        """
        return self._get(
            "/geo/1.0/reverse",
            params={"lat": lat, "lon": lon, "limit": limit, "appid": self.api_key},
            is_list=True,
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, is_list: bool = False, **kwargs) -> dict | list:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
