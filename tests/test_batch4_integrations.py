"""Tests for batch 4 integrations: Notion AI, Perplexity Search, Brave Search,
Wikipedia, Weather, News API, Google Maps, Yelp, OpenSea, Binance."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Notion AI
# ---------------------------------------------------------------------------


class TestNotionAIClient:
    @patch("goliath.integrations.notion_ai.config")
    def test_missing_token_raises(self, mock_config):
        mock_config.NOTION_AI_API_KEY = ""
        mock_config.NOTION_API_KEY = ""

        from goliath.integrations.notion_ai import NotionAIClient

        with pytest.raises(RuntimeError, match="NOTION_AI_API_KEY"):
            NotionAIClient()

    @patch("goliath.integrations.notion_ai.requests")
    @patch("goliath.integrations.notion_ai.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.NOTION_AI_API_KEY = "ntn_test_tok"
        mock_config.NOTION_API_KEY = ""

        from goliath.integrations.notion_ai import NotionAIClient

        client = NotionAIClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer ntn_test_tok"
        assert call_kwargs["Notion-Version"] == "2022-06-28"

    @patch("goliath.integrations.notion_ai.requests")
    @patch("goliath.integrations.notion_ai.config")
    def test_falls_back_to_notion_api_key(self, mock_config, mock_requests):
        mock_config.NOTION_AI_API_KEY = ""
        mock_config.NOTION_API_KEY = "ntn_fallback"

        from goliath.integrations.notion_ai import NotionAIClient

        client = NotionAIClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer ntn_fallback"

    @patch("goliath.integrations.notion_ai.requests")
    @patch("goliath.integrations.notion_ai.config")
    def test_generate(self, mock_config, mock_requests):
        mock_config.NOTION_AI_API_KEY = "tok"
        mock_config.NOTION_API_KEY = ""

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"completion": "Generated text here."}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.notion_ai import NotionAIClient

        client = NotionAIClient()
        result = client.generate(prompt="Write a haiku about AI")

        assert result == "Generated text here."
        url = client.session.post.call_args[0][0]
        assert "/ai/completions" in url

    @patch("goliath.integrations.notion_ai.requests")
    @patch("goliath.integrations.notion_ai.config")
    def test_summarize(self, mock_config, mock_requests):
        mock_config.NOTION_AI_API_KEY = "tok"
        mock_config.NOTION_API_KEY = ""

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"completion": "Short summary."}
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.notion_ai import NotionAIClient

        client = NotionAIClient()
        result = client.summarize(text="Long text that needs summarizing...")

        assert result == "Short summary."
        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["action"] == "summarize"

    @patch("goliath.integrations.notion_ai.requests")
    @patch("goliath.integrations.notion_ai.config")
    def test_fallback_on_404(self, mock_config, mock_requests):
        mock_config.NOTION_AI_API_KEY = "tok"
        mock_config.NOTION_API_KEY = ""

        # First call: AI completion returns 404
        ai_resp = MagicMock()
        ai_resp.status_code = 404

        # Second call: fallback comment
        comment_resp = MagicMock()
        comment_resp.json.return_value = {"id": "comment_123"}
        comment_resp.raise_for_status = MagicMock()

        mock_requests.Session.return_value.post.side_effect = [ai_resp, comment_resp]

        from goliath.integrations.notion_ai import NotionAIClient

        client = NotionAIClient()
        result = client.generate(prompt="Write something", page_id="page_abc")

        assert result == "comment_123"


# ---------------------------------------------------------------------------
# Perplexity Search
# ---------------------------------------------------------------------------


class TestPerplexitySearchClient:
    @patch("goliath.integrations.perplexity_search.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.PERPLEXITY_API_KEY = ""

        from goliath.integrations.perplexity_search import PerplexitySearchClient

        with pytest.raises(RuntimeError, match="PERPLEXITY_API_KEY"):
            PerplexitySearchClient()

    @patch("goliath.integrations.perplexity_search.requests")
    @patch("goliath.integrations.perplexity_search.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.PERPLEXITY_API_KEY = "pplx_test"

        from goliath.integrations.perplexity_search import PerplexitySearchClient

        client = PerplexitySearchClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer pplx_test"

    @patch("goliath.integrations.perplexity_search.requests")
    @patch("goliath.integrations.perplexity_search.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.PERPLEXITY_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Bitcoin is $50,000."}}],
            "citations": ["https://example.com/btc"],
            "model": "sonar",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.perplexity_search import PerplexitySearchClient

        client = PerplexitySearchClient()
        result = client.search("What is the price of Bitcoin?")

        assert result["answer"] == "Bitcoin is $50,000."
        assert result["citations"] == ["https://example.com/btc"]
        url = client.session.post.call_args[0][0]
        assert "/chat/completions" in url

    @patch("goliath.integrations.perplexity_search.requests")
    @patch("goliath.integrations.perplexity_search.config")
    def test_quick_search(self, mock_config, mock_requests):
        mock_config.PERPLEXITY_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Quick answer."}}],
            "citations": [],
            "model": "sonar",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.perplexity_search import PerplexitySearchClient

        client = PerplexitySearchClient()
        answer = client.quick_search("Tell me about Python")

        assert answer == "Quick answer."

    @patch("goliath.integrations.perplexity_search.requests")
    @patch("goliath.integrations.perplexity_search.config")
    def test_search_with_recency_filter(self, mock_config, mock_requests):
        mock_config.PERPLEXITY_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Recent news."}}],
            "citations": [],
            "model": "sonar",
        }
        mock_requests.Session.return_value.post.return_value = mock_resp

        from goliath.integrations.perplexity_search import PerplexitySearchClient

        client = PerplexitySearchClient()
        client.search("tech news", recency_filter="day")

        payload = client.session.post.call_args.kwargs.get(
            "json", client.session.post.call_args[1].get("json", {})
        )
        assert payload["search_recency_filter"] == "day"


# ---------------------------------------------------------------------------
# Brave Search
# ---------------------------------------------------------------------------


class TestBraveSearchClient:
    @patch("goliath.integrations.brave_search.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.BRAVE_SEARCH_API_KEY = ""

        from goliath.integrations.brave_search import BraveSearchClient

        with pytest.raises(RuntimeError, match="BRAVE_SEARCH_API_KEY"):
            BraveSearchClient()

    @patch("goliath.integrations.brave_search.requests")
    @patch("goliath.integrations.brave_search.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.BRAVE_SEARCH_API_KEY = "BSA_test"

        from goliath.integrations.brave_search import BraveSearchClient

        client = BraveSearchClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-Subscription-Token"] == "BSA_test"

    @patch("goliath.integrations.brave_search.requests")
    @patch("goliath.integrations.brave_search.config")
    def test_web_search(self, mock_config, mock_requests):
        mock_config.BRAVE_SEARCH_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "web": {"results": [{"title": "Result 1", "url": "https://example.com"}]}
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.brave_search import BraveSearchClient

        client = BraveSearchClient()
        results = client.web_search("Python tutorial", count=5)

        assert "web" in results
        url = client.session.get.call_args[0][0]
        assert "/web/search" in url

    @patch("goliath.integrations.brave_search.requests")
    @patch("goliath.integrations.brave_search.config")
    def test_news_search(self, mock_config, mock_requests):
        mock_config.BRAVE_SEARCH_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"title": "News Article", "url": "https://news.example.com"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.brave_search import BraveSearchClient

        client = BraveSearchClient()
        results = client.news_search("AI regulation")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/news/search" in url

    @patch("goliath.integrations.brave_search.requests")
    @patch("goliath.integrations.brave_search.config")
    def test_image_search(self, mock_config, mock_requests):
        mock_config.BRAVE_SEARCH_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"title": "Image", "url": "https://img.example.com/1.jpg"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.brave_search import BraveSearchClient

        client = BraveSearchClient()
        results = client.image_search("aurora borealis")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/images/search" in url


# ---------------------------------------------------------------------------
# Wikipedia
# ---------------------------------------------------------------------------


class TestWikipediaClient:
    @patch("goliath.integrations.wikipedia.requests")
    @patch("goliath.integrations.wikipedia.config")
    def test_no_auth_required(self, mock_config, mock_requests):
        mock_config.WIKIPEDIA_USER_AGENT = ""
        mock_config.WIKIPEDIA_ACCESS_TOKEN = ""

        from goliath.integrations.wikipedia import WikipediaClient

        client = WikipediaClient()
        # Should init without raising
        assert "en.wikipedia.org" in client._base

    @patch("goliath.integrations.wikipedia.requests")
    @patch("goliath.integrations.wikipedia.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.WIKIPEDIA_USER_AGENT = ""
        mock_config.WIKIPEDIA_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "pages": [{"title": "Artificial intelligence", "description": "Field of CS"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.wikipedia import WikipediaClient

        client = WikipediaClient()
        results = client.search("artificial intelligence")

        assert len(results) == 1
        assert results[0]["title"] == "Artificial intelligence"
        url = client.session.get.call_args[0][0]
        assert "/search/page" in url

    @patch("goliath.integrations.wikipedia.requests")
    @patch("goliath.integrations.wikipedia.config")
    def test_get_summary(self, mock_config, mock_requests):
        mock_config.WIKIPEDIA_USER_AGENT = ""
        mock_config.WIKIPEDIA_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "title": "Python (programming language)",
            "extract": "Python is a programming language.",
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.wikipedia import WikipediaClient

        client = WikipediaClient()
        summary = client.get_summary("Python_(programming_language)")

        assert summary["title"] == "Python (programming language)"
        url = client.session.get.call_args[0][0]
        assert "/page/summary/" in url

    @patch("goliath.integrations.wikipedia.requests")
    @patch("goliath.integrations.wikipedia.config")
    def test_random_summary(self, mock_config, mock_requests):
        mock_config.WIKIPEDIA_USER_AGENT = ""
        mock_config.WIKIPEDIA_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "title": "Random Article",
            "extract": "Random content.",
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.wikipedia import WikipediaClient

        client = WikipediaClient()
        summary = client.random_summary()

        assert summary["title"] == "Random Article"
        url = client.session.get.call_args[0][0]
        assert "/page/random/summary" in url

    @patch("goliath.integrations.wikipedia.requests")
    @patch("goliath.integrations.wikipedia.config")
    def test_on_this_day(self, mock_config, mock_requests):
        mock_config.WIKIPEDIA_USER_AGENT = ""
        mock_config.WIKIPEDIA_ACCESS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "events": [{"text": "Something happened", "year": 1969}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.wikipedia import WikipediaClient

        client = WikipediaClient()
        events = client.on_this_day(month=7, day=20)

        assert len(events) == 1
        url = client.session.get.call_args[0][0]
        assert "/feed/onthisday/" in url


# ---------------------------------------------------------------------------
# Weather (OpenWeatherMap)
# ---------------------------------------------------------------------------


class TestWeatherClient:
    @patch("goliath.integrations.weather.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.OPENWEATHER_API_KEY = ""

        from goliath.integrations.weather import WeatherClient

        with pytest.raises(RuntimeError, match="OPENWEATHER_API_KEY"):
            WeatherClient()

    @patch("goliath.integrations.weather.requests")
    @patch("goliath.integrations.weather.config")
    def test_get_current(self, mock_config, mock_requests):
        mock_config.OPENWEATHER_API_KEY = "owm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "main": {"temp": 15.5, "humidity": 60},
            "weather": [{"description": "clear sky"}],
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.weather import WeatherClient

        client = WeatherClient()
        weather = client.get_current("London")

        assert weather["main"]["temp"] == 15.5
        url = client.session.get.call_args[0][0]
        assert "/data/2.5/weather" in url

    @patch("goliath.integrations.weather.requests")
    @patch("goliath.integrations.weather.config")
    def test_get_current_by_coords(self, mock_config, mock_requests):
        mock_config.OPENWEATHER_API_KEY = "owm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"main": {"temp": 22.0}}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.weather import WeatherClient

        client = WeatherClient()
        weather = client.get_current_by_coords(lat=51.5074, lon=-0.1278)

        assert weather["main"]["temp"] == 22.0
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["lat"] == 51.5074
        assert params["lon"] == -0.1278

    @patch("goliath.integrations.weather.requests")
    @patch("goliath.integrations.weather.config")
    def test_get_forecast(self, mock_config, mock_requests):
        mock_config.OPENWEATHER_API_KEY = "owm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "list": [{"dt": 1700000000, "main": {"temp": 10}}, {"dt": 1700010000, "main": {"temp": 12}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.weather import WeatherClient

        client = WeatherClient()
        forecast = client.get_forecast("New York", units="imperial")

        assert len(forecast["list"]) == 2
        url = client.session.get.call_args[0][0]
        assert "/data/2.5/forecast" in url

    @patch("goliath.integrations.weather.requests")
    @patch("goliath.integrations.weather.config")
    def test_geocode(self, mock_config, mock_requests):
        mock_config.OPENWEATHER_API_KEY = "owm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "JP"}
        ]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.weather import WeatherClient

        client = WeatherClient()
        locations = client.geocode("Tokyo")

        assert len(locations) == 1
        assert locations[0]["name"] == "Tokyo"
        url = client.session.get.call_args[0][0]
        assert "/geo/1.0/direct" in url

    @patch("goliath.integrations.weather.requests")
    @patch("goliath.integrations.weather.config")
    def test_air_quality(self, mock_config, mock_requests):
        mock_config.OPENWEATHER_API_KEY = "owm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "list": [{"main": {"aqi": 2}, "components": {"co": 230}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.weather import WeatherClient

        client = WeatherClient()
        aqi = client.get_air_quality(lat=40.7128, lon=-74.0060)

        assert aqi["list"][0]["main"]["aqi"] == 2
        url = client.session.get.call_args[0][0]
        assert "/data/2.5/air_pollution" in url


# ---------------------------------------------------------------------------
# News API
# ---------------------------------------------------------------------------


class TestNewsClient:
    @patch("goliath.integrations.news.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.NEWS_API_KEY = ""

        from goliath.integrations.news import NewsClient

        with pytest.raises(RuntimeError, match="NEWS_API_KEY"):
            NewsClient()

    @patch("goliath.integrations.news.requests")
    @patch("goliath.integrations.news.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.NEWS_API_KEY = "news_key"

        from goliath.integrations.news import NewsClient

        client = NewsClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-Api-Key"] == "news_key"

    @patch("goliath.integrations.news.requests")
    @patch("goliath.integrations.news.config")
    def test_top_headlines(self, mock_config, mock_requests):
        mock_config.NEWS_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [{"title": "Tech News", "source": {"name": "TechCrunch"}}],
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.news import NewsClient

        client = NewsClient()
        headlines = client.top_headlines(country="us", category="technology")

        assert headlines["totalResults"] == 1
        url = client.session.get.call_args[0][0]
        assert "/top-headlines" in url

    @patch("goliath.integrations.news.requests")
    @patch("goliath.integrations.news.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.NEWS_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [{"title": "Article 1"}, {"title": "Article 2"}],
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.news import NewsClient

        client = NewsClient()
        articles = client.search("artificial intelligence", sort_by="relevancy")

        assert articles["totalResults"] == 2
        url = client.session.get.call_args[0][0]
        assert "/everything" in url

    @patch("goliath.integrations.news.requests")
    @patch("goliath.integrations.news.config")
    def test_get_sources(self, mock_config, mock_requests):
        mock_config.NEWS_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "ok",
            "sources": [{"id": "bbc-news", "name": "BBC News"}],
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.news import NewsClient

        client = NewsClient()
        sources = client.get_sources(language="en")

        assert len(sources) == 1
        assert sources[0]["id"] == "bbc-news"


# ---------------------------------------------------------------------------
# Google Maps
# ---------------------------------------------------------------------------


class TestGoogleMapsClient:
    @patch("goliath.integrations.google_maps.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.GOOGLE_MAPS_API_KEY = ""

        from goliath.integrations.google_maps import GoogleMapsClient

        with pytest.raises(RuntimeError, match="GOOGLE_MAPS_API_KEY"):
            GoogleMapsClient()

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_geocode(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"formatted_address": "1600 Amphitheatre Parkway", "geometry": {"location": {"lat": 37.42, "lng": -122.08}}}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        results = client.geocode("1600 Amphitheatre Parkway")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/geocode/json" in url

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_reverse_geocode(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"formatted_address": "Mountain View, CA"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        results = client.reverse_geocode(lat=37.42, lng=-122.08)

        assert len(results) == 1
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert "37.42,-122.08" in params["latlng"]

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_nearby_search(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"name": "Blue Bottle Coffee", "rating": 4.5}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        places = client.nearby_search(lat=40.7128, lng=-74.0060, radius=1000, keyword="coffee")

        assert places["results"][0]["name"] == "Blue Bottle Coffee"
        url = client.session.get.call_args[0][0]
        assert "/place/nearbysearch/json" in url

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_directions(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "routes": [{"legs": [{"distance": {"text": "216 mi"}, "duration": {"text": "3 hours 45 mins"}}]}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        routes = client.directions(origin="New York, NY", destination="Boston, MA")

        assert len(routes) == 1
        url = client.session.get.call_args[0][0]
        assert "/directions/json" in url

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_distance_matrix(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "rows": [{"elements": [{"distance": {"text": "216 mi"}, "status": "OK"}]}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        matrix = client.distance_matrix(
            origins=["New York, NY"],
            destinations=["Boston, MA"],
        )

        assert matrix["rows"][0]["elements"][0]["status"] == "OK"
        url = client.session.get.call_args[0][0]
        assert "/distancematrix/json" in url
        params = client.session.get.call_args.kwargs.get(
            "params", client.session.get.call_args[1].get("params", {})
        )
        assert params["origins"] == "New York, NY"

    @patch("goliath.integrations.google_maps.requests")
    @patch("goliath.integrations.google_maps.config")
    def test_autocomplete(self, mock_config, mock_requests):
        mock_config.GOOGLE_MAPS_API_KEY = "gm_key"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "predictions": [{"description": "Starbucks, Times Square"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.google_maps import GoogleMapsClient

        client = GoogleMapsClient()
        predictions = client.autocomplete("starb")

        assert len(predictions) == 1
        url = client.session.get.call_args[0][0]
        assert "/place/autocomplete/json" in url


# ---------------------------------------------------------------------------
# Yelp
# ---------------------------------------------------------------------------


class TestYelpClient:
    @patch("goliath.integrations.yelp.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.YELP_API_KEY = ""

        from goliath.integrations.yelp import YelpClient

        with pytest.raises(RuntimeError, match="YELP_API_KEY"):
            YelpClient()

    @patch("goliath.integrations.yelp.requests")
    @patch("goliath.integrations.yelp.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.YELP_API_KEY = "yelp_tok"

        from goliath.integrations.yelp import YelpClient

        client = YelpClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["Authorization"] == "Bearer yelp_tok"

    @patch("goliath.integrations.yelp.requests")
    @patch("goliath.integrations.yelp.config")
    def test_search(self, mock_config, mock_requests):
        mock_config.YELP_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "businesses": [{"name": "Blue Bottle Coffee", "rating": 4.5}],
            "total": 1,
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.yelp import YelpClient

        client = YelpClient()
        results = client.search("coffee", location="San Francisco, CA")

        assert results["total"] == 1
        url = client.session.get.call_args[0][0]
        assert "/businesses/search" in url

    @patch("goliath.integrations.yelp.requests")
    @patch("goliath.integrations.yelp.config")
    def test_get_business(self, mock_config, mock_requests):
        mock_config.YELP_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": "north-india-restaurant-sf",
            "name": "North India Restaurant",
            "rating": 4.0,
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.yelp import YelpClient

        client = YelpClient()
        biz = client.get_business("north-india-restaurant-sf")

        assert biz["name"] == "North India Restaurant"
        url = client.session.get.call_args[0][0]
        assert "/businesses/north-india-restaurant-sf" in url

    @patch("goliath.integrations.yelp.requests")
    @patch("goliath.integrations.yelp.config")
    def test_get_reviews(self, mock_config, mock_requests):
        mock_config.YELP_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "reviews": [{"rating": 5, "text": "Amazing!"}],
            "total": 1,
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.yelp import YelpClient

        client = YelpClient()
        reviews = client.get_reviews("north-india-restaurant-sf")

        assert len(reviews) == 1
        assert reviews[0]["rating"] == 5
        url = client.session.get.call_args[0][0]
        assert "/businesses/north-india-restaurant-sf/reviews" in url

    @patch("goliath.integrations.yelp.requests")
    @patch("goliath.integrations.yelp.config")
    def test_phone_search(self, mock_config, mock_requests):
        mock_config.YELP_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "businesses": [{"name": "Some Restaurant"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.yelp import YelpClient

        client = YelpClient()
        results = client.phone_search("+14155551234")

        assert len(results) == 1
        url = client.session.get.call_args[0][0]
        assert "/businesses/search/phone" in url


# ---------------------------------------------------------------------------
# OpenSea
# ---------------------------------------------------------------------------


class TestOpenSeaClient:
    @patch("goliath.integrations.opensea.config")
    def test_missing_key_raises(self, mock_config):
        mock_config.OPENSEA_API_KEY = ""

        from goliath.integrations.opensea import OpenSeaClient

        with pytest.raises(RuntimeError, match="OPENSEA_API_KEY"):
            OpenSeaClient()

    @patch("goliath.integrations.opensea.requests")
    @patch("goliath.integrations.opensea.config")
    def test_headers_set(self, mock_config, mock_requests):
        mock_config.OPENSEA_API_KEY = "os_key"

        from goliath.integrations.opensea import OpenSeaClient

        client = OpenSeaClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-API-KEY"] == "os_key"

    @patch("goliath.integrations.opensea.requests")
    @patch("goliath.integrations.opensea.config")
    def test_get_collection(self, mock_config, mock_requests):
        mock_config.OPENSEA_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "collection": "boredapeyachtclub",
            "name": "Bored Ape Yacht Club",
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.opensea import OpenSeaClient

        client = OpenSeaClient()
        collection = client.get_collection("boredapeyachtclub")

        assert collection["name"] == "Bored Ape Yacht Club"
        url = client.session.get.call_args[0][0]
        assert "/collections/boredapeyachtclub" in url

    @patch("goliath.integrations.opensea.requests")
    @patch("goliath.integrations.opensea.config")
    def test_get_nfts(self, mock_config, mock_requests):
        mock_config.OPENSEA_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "nfts": [{"identifier": "1", "name": "Ape #1"}],
            "next": "cursor_abc",
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.opensea import OpenSeaClient

        client = OpenSeaClient()
        result = client.get_nfts(collection_slug="boredapeyachtclub", limit=10)

        assert len(result["nfts"]) == 1
        assert result["next"] == "cursor_abc"
        url = client.session.get.call_args[0][0]
        assert "/collection/boredapeyachtclub/nfts" in url

    @patch("goliath.integrations.opensea.requests")
    @patch("goliath.integrations.opensea.config")
    def test_get_collection_stats(self, mock_config, mock_requests):
        mock_config.OPENSEA_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "total": {"volume": 685000, "sales": 32000, "floor_price": 28.5}
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.opensea import OpenSeaClient

        client = OpenSeaClient()
        stats = client.get_collection_stats("boredapeyachtclub")

        assert stats["total"]["floor_price"] == 28.5
        url = client.session.get.call_args[0][0]
        assert "/collections/boredapeyachtclub/stats" in url

    @patch("goliath.integrations.opensea.requests")
    @patch("goliath.integrations.opensea.config")
    def test_list_events(self, mock_config, mock_requests):
        mock_config.OPENSEA_API_KEY = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "asset_events": [{"event_type": "sale", "total_price": "50000000000000000000"}]
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.opensea import OpenSeaClient

        client = OpenSeaClient()
        events = client.list_events(collection_slug="boredapeyachtclub", event_type="sale")

        assert events["asset_events"][0]["event_type"] == "sale"
        url = client.session.get.call_args[0][0]
        assert "/events" in url


# ---------------------------------------------------------------------------
# Binance
# ---------------------------------------------------------------------------


class TestBinanceClient:
    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_no_key_init_allowed(self, mock_config, mock_requests):
        """Binance allows init without keys for public market data endpoints."""
        mock_config.BINANCE_API_KEY = ""
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        # Should init without raising
        assert client.api_key == ""

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_api_key_header_set(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "bnc_key"
        mock_config.BINANCE_API_SECRET = "bnc_secret"
        mock_config.BINANCE_BASE_URL = ""

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        call_kwargs = client.session.headers.update.call_args[0][0]
        assert call_kwargs["X-MBX-APIKEY"] == "bnc_key"

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_get_price(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "key"
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"symbol": "BTCUSDT", "price": "50123.45"}
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        price = client.get_price("BTCUSDT")

        assert price["symbol"] == "BTCUSDT"
        assert price["price"] == "50123.45"
        url = client.session.get.call_args[0][0]
        assert "/api/v3/ticker/price" in url

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_get_order_book(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "key"
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "bids": [["50000.00", "1.5"]],
            "asks": [["50001.00", "0.8"]],
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        book = client.get_order_book("ETHUSDT", limit=10)

        assert len(book["bids"]) == 1
        assert len(book["asks"]) == 1
        url = client.session.get.call_args[0][0]
        assert "/api/v3/depth" in url

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_get_klines(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "key"
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            [1700000000000, "50000", "51000", "49000", "50500", "100"],
        ]
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        klines = client.get_klines("BTCUSDT", interval="1h", limit=24)

        assert len(klines) == 1
        url = client.session.get.call_args[0][0]
        assert "/api/v3/klines" in url

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_signed_request_requires_secret(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "key"
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        with pytest.raises(RuntimeError, match="BINANCE_API_KEY and BINANCE_API_SECRET"):
            client.get_account()

    @patch("goliath.integrations.binance.requests")
    @patch("goliath.integrations.binance.config")
    def test_get_24h_stats(self, mock_config, mock_requests):
        mock_config.BINANCE_API_KEY = "key"
        mock_config.BINANCE_API_SECRET = ""
        mock_config.BINANCE_BASE_URL = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "symbol": "BTCUSDT",
            "priceChange": "1500.00",
            "volume": "50000",
        }
        mock_requests.Session.return_value.get.return_value = mock_resp

        from goliath.integrations.binance import BinanceClient

        client = BinanceClient()
        stats = client.get_24h_stats("BTCUSDT")

        assert stats["symbol"] == "BTCUSDT"
        url = client.session.get.call_args[0][0]
        assert "/api/v3/ticker/24hr" in url
