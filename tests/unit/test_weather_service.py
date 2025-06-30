"""Tests for weather service."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError

from src.core.weather_service import WeatherService, WeatherSummary
from src.models import WeatherAPIError


class TestWeatherService:
    """Test cases for WeatherService."""

    @pytest.fixture
    def weather_service(self, monkeypatch):
        """Create a weather service instance."""
        # WeatherServiceを作成する前にsettingsをモック
        monkeypatch.setattr("src.core.weather_service.settings.WEATHER_API_KEY", "test_api_key")
        monkeypatch.setattr("src.core.weather_service.settings.ENABLE_WEATHER_API", True)

        service = WeatherService()
        # 作成後にもAPI keyを設定（念のため）
        service.api_key = "test_api_key"
        return service

    @pytest.fixture
    def mock_weather_response(self):
        """Mock weather API response."""
        return {
            "list": [
                {
                    "dt": 1719763200,  # 2024-07-01 00:00:00
                    "main": {
                        "temp": 25.5,
                        "feels_like": 26.0,
                        "temp_min": 23.0,
                        "temp_max": 28.0,
                        "humidity": 60,
                    },
                    "weather": [{"main": "Clear", "description": "晴れ"}],
                    "wind": {"speed": 3.5},
                    "pop": 0.1,
                },
                {
                    "dt": 1719774000,  # 2024-07-01 03:00:00
                    "main": {
                        "temp": 24.0,
                        "feels_like": 24.5,
                        "temp_min": 22.0,
                        "temp_max": 26.0,
                        "humidity": 65,
                    },
                    "weather": [{"main": "Clouds", "description": "曇り"}],
                    "wind": {"speed": 2.5},
                    "pop": 0.2,
                },
            ]
        }

    @pytest.fixture
    def mock_geocoding_response(self):
        """Mock geocoding API response."""
        return [
            {
                "name": "Tokyo",
                "local_names": {"ja": "東京"},
                "lat": 35.6762,
                "lon": 139.6503,
                "country": "JP",
            }
        ]

    @pytest.mark.asyncio
    async def test_get_weather_summary_success(
        self, weather_service, mock_weather_response, mock_geocoding_response
    ):
        """Test successful weather summary retrieval."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Mock the session
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock geocoding response
            mock_geo_response = AsyncMock()
            mock_geo_response.status = 200
            mock_geo_response.json = AsyncMock(return_value=mock_geocoding_response)
            mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
            mock_geo_response.__aexit__ = AsyncMock(return_value=None)

            # Mock weather response
            mock_weather_response_obj = AsyncMock()
            mock_weather_response_obj.status = 200
            mock_weather_response_obj.json = AsyncMock(return_value=mock_weather_response)
            mock_weather_response_obj.__aenter__ = AsyncMock(return_value=mock_weather_response_obj)
            mock_weather_response_obj.__aexit__ = AsyncMock(return_value=None)

            # Create a function that returns different responses based on URL
            def get_response(url, **kwargs):
                if "geo" in url:
                    return mock_geo_response
                else:
                    return mock_weather_response_obj

            # Assign the function directly (not as side_effect)
            mock_session.get = get_response

            # Test the method
            summary = await weather_service.get_weather_summary(
                "Tokyo", date(2024, 7, 1), date(2024, 7, 1)
            )

            # Verify the result
            assert isinstance(summary, WeatherSummary)
            assert summary.location == "東京"
            assert summary.start_date == date(2024, 7, 1)
            assert summary.end_date == date(2024, 7, 1)
            assert len(summary.daily_forecasts) == 1
            assert summary.has_rain is False
            assert summary.min_temperature == 24.0  # Min of temps: 25.5, 24.0
            assert summary.max_temperature == 25.5  # Max of temps: 25.5, 24.0
            assert summary.max_rain_probability == 20.0

    @pytest.mark.asyncio
    async def test_get_weather_summary_api_disabled(self):
        """Test weather summary when API is disabled."""
        with patch("src.core.weather_service.settings") as mock_settings:
            mock_settings.WEATHER_API_KEY = None
            mock_settings.ENABLE_WEATHER_API = False
            service = WeatherService()

            with pytest.raises(WeatherAPIError, match="Weather API is not configured"):
                await service.get_weather_summary("Tokyo", date.today(), date.today())

    @pytest.mark.asyncio
    async def test_get_weather_summary_location_not_found(self, weather_service):
        """Test weather summary when location is not found."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock empty geocoding response
            mock_geo_response = AsyncMock()
            mock_geo_response.status = 200
            mock_geo_response.json = AsyncMock(return_value=[])
            mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
            mock_geo_response.__aexit__ = AsyncMock(return_value=None)

            # Configure get to return the response directly (not as a coroutine)
            mock_session.get = lambda *args, **kwargs: mock_geo_response

            with pytest.raises(WeatherAPIError, match="Location not found"):
                await weather_service.get_weather_summary(
                    "NonexistentCity", date.today(), date.today()
                )

    @pytest.mark.asyncio
    async def test_get_weather_summary_api_error(self, weather_service):
        """Test weather summary when API returns an error."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock API error response
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            # Configure get to return the response directly (not as a coroutine)
            mock_session.get = lambda *args, **kwargs: mock_response

            with pytest.raises(WeatherAPIError, match="Geocoding API error"):
                await weather_service.get_weather_summary("Tokyo", date.today(), date.today())

    @pytest.mark.asyncio
    async def test_get_weather_summary_network_error(self, weather_service):
        """Test weather summary when network error occurs."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock network error - use a function that raises the exception
            def raise_network_error(*args, **kwargs):
                raise ClientError("Network error")

            mock_session.get = raise_network_error

            with pytest.raises(WeatherAPIError, match="Failed to fetch weather data"):
                await weather_service.get_weather_summary("Tokyo", date.today(), date.today())

    @pytest.mark.asyncio
    async def test_weather_summary_with_rain(self, weather_service, mock_geocoding_response):
        """Test weather summary with rain conditions."""
        rain_response = {
            "list": [
                {
                    "dt": 1719763200,
                    "main": {
                        "temp": 20.0,
                        "feels_like": 19.0,
                        "temp_min": 18.0,
                        "temp_max": 22.0,
                        "humidity": 80,
                    },
                    "weather": [{"main": "Rain", "description": "雨"}],
                    "wind": {"speed": 5.0},
                    "pop": 0.8,  # 80% rain probability
                }
            ]
        }

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mock responses
            mock_geo_response = AsyncMock()
            mock_geo_response.status = 200
            mock_geo_response.json = AsyncMock(return_value=mock_geocoding_response)
            mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
            mock_geo_response.__aexit__ = AsyncMock(return_value=None)

            mock_weather_response = AsyncMock()
            mock_weather_response.status = 200
            mock_weather_response.json = AsyncMock(return_value=rain_response)
            mock_weather_response.__aenter__ = AsyncMock(return_value=mock_weather_response)
            mock_weather_response.__aexit__ = AsyncMock(return_value=None)

            # Configure get to return different responses based on call order
            responses = [mock_geo_response, mock_weather_response]
            mock_session.get = lambda *args, **kwargs: responses.pop(0)

            summary = await weather_service.get_weather_summary(
                "Tokyo", date(2024, 7, 1), date(2024, 7, 1)
            )

            assert summary.has_rain is True
            assert summary.max_rain_probability == 80.0
            assert "Rain" in summary.weather_conditions

    def test_cache_functionality(self, weather_service):
        """Test cache functionality."""
        # Create a mock summary
        summary = WeatherSummary(
            location="Tokyo",
            start_date=date.today(),
            end_date=date.today(),
            daily_forecasts=[],
            has_rain=False,
            min_temperature=20.0,
            max_temperature=25.0,
            avg_temperature=22.5,
            max_rain_probability=0,
            weather_conditions=["Clear"],
        )

        # Save to cache
        cache_key = "Tokyo_2024-07-01_2024-07-01"
        weather_service._save_to_cache(cache_key, summary)

        # Retrieve from cache
        cached = weather_service._get_from_cache(cache_key)
        assert cached is not None
        assert cached.location == "Tokyo"

        # Test cache expiration
        # Manually set old timestamp
        weather_service._cache[cache_key] = (
            summary,
            datetime.now() - timedelta(hours=2),
        )
        cached = weather_service._get_from_cache(cache_key)
        assert cached is None

    @pytest.mark.asyncio
    async def test_weather_summary_with_cache_hit(
        self, weather_service, mock_geocoding_response, mock_weather_response
    ):
        """Test weather summary retrieval with cache hit."""
        # First call - should hit the API
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_geo_response = AsyncMock()
            mock_geo_response.status = 200
            mock_geo_response.json = AsyncMock(return_value=mock_geocoding_response)
            mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
            mock_geo_response.__aexit__ = AsyncMock(return_value=None)

            mock_weather_response_obj = AsyncMock()
            mock_weather_response_obj.status = 200
            mock_weather_response_obj.json = AsyncMock(return_value=mock_weather_response)
            mock_weather_response_obj.__aenter__ = AsyncMock(return_value=mock_weather_response_obj)
            mock_weather_response_obj.__aexit__ = AsyncMock(return_value=None)

            # Configure get to return different responses based on call order
            responses = [mock_geo_response, mock_weather_response_obj]
            mock_session.get = lambda *args, **kwargs: responses.pop(0)

            # First call
            summary1 = await weather_service.get_weather_summary(
                "Tokyo", date(2024, 7, 1), date(2024, 7, 1)
            )

        # Second call - should use cache
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # This should not be called due to cache
            summary2 = await weather_service.get_weather_summary(
                "Tokyo", date(2024, 7, 1), date(2024, 7, 1)
            )

            # Verify no API calls were made
            mock_session.get.assert_not_called()

        # Verify both summaries are the same
        assert summary1.location == summary2.location
        assert summary1.max_temperature == summary2.max_temperature
