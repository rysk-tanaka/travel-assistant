"""
Weather service for fetching weather data from OpenWeatherMap API.

このモジュールは、OpenWeatherMap APIを使用して天気予報データを取得し、
旅行準備のための天気情報を提供します。
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp
from pydantic import BaseModel

from src.config.settings import settings
from src.models import WeatherAPIError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class Coordinates(BaseModel):
    """地理座標."""

    lat: float
    lon: float
    city_name: str
    country: str


class WeatherData(BaseModel):
    """天気データ."""

    date: date
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    rain_probability: float
    weather_condition: str
    weather_description: str
    wind_speed: float
    uv_index: float | None = None


class WeatherSummary(BaseModel):
    """旅行期間の天気サマリー."""

    location: str
    start_date: date
    end_date: date
    daily_forecasts: list[WeatherData]
    has_rain: bool
    min_temperature: float
    max_temperature: float
    avg_temperature: float
    max_rain_probability: float
    weather_conditions: list[str]  # ユニークな天気条件


class WeatherService:
    """OpenWeatherMap APIを使用した天気予報サービス."""

    def __init__(self) -> None:
        """WeatherServiceを初期化."""
        self.api_key: str | None = settings.WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geocoding_url = "https://api.openweathermap.org/geo/1.0"
        self._cache: dict[str, tuple[WeatherSummary, datetime]] = {}
        self._cache_duration = timedelta(hours=1)

    async def get_weather_summary(
        self, location: str, start_date: date, end_date: date
    ) -> WeatherSummary:
        """指定期間の天気サマリーを取得.

        Args:
            location: 都市名（例: "札幌", "Tokyo"）
            start_date: 開始日
            end_date: 終了日

        Returns:
            WeatherSummary: 期間中の天気サマリー

        Raises:
            WeatherAPIError: API呼び出しに失敗した場合
        """
        if not self.api_key or not settings.ENABLE_WEATHER_API:
            logger.warning("Weather API is disabled or API key is not set")
            raise WeatherAPIError("Weather API is not configured")

        # キャッシュチェック
        cache_key = f"{location}_{start_date}_{end_date}"
        if cached := self._get_from_cache(cache_key):
            logger.debug(f"Returning cached weather data for {location}")
            return cached

        try:
            # 座標取得
            coords = await self._get_coordinates(location)
            logger.info(f"Got coordinates for {location}: {coords.lat}, {coords.lon}")

            # 天気予報取得
            forecasts = await self._fetch_forecast(coords, start_date, end_date)

            # サマリー作成
            summary = self._create_summary(coords.city_name, start_date, end_date, forecasts)

            # キャッシュに保存
            self._save_to_cache(cache_key, summary)

            return summary

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch weather data: {e}")
            raise WeatherAPIError(f"Failed to fetch weather data for {location}") from e
        except Exception as e:
            logger.error(f"Unexpected error in weather service: {e}")
            raise WeatherAPIError(f"Weather service error: {e}") from e

    async def _get_coordinates(self, location: str) -> Coordinates:
        """都市名から座標を取得."""
        # この時点でapi_keyは必ず存在する（get_weather_summaryでチェック済み）
        assert self.api_key is not None

        params: dict[str, str | int] = {
            "q": location,
            "limit": 1,
            "appid": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.geocoding_url + "/direct", params=params) as response:
                if response.status != 200:
                    raise WeatherAPIError(f"Geocoding API error: {response.status}")

                data = await response.json()
                if not data:
                    raise WeatherAPIError(f"Location not found: {location}")

                result = data[0]
                return Coordinates(
                    lat=result["lat"],
                    lon=result["lon"],
                    city_name=result.get("local_names", {}).get("ja", result["name"]),
                    country=result["country"],
                )

    async def _fetch_forecast(
        self, coords: Coordinates, start_date: date, end_date: date
    ) -> list[WeatherData]:
        """5日間の天気予報を取得."""
        # この時点でapi_keyは必ず存在する（get_weather_summaryでチェック済み）
        assert self.api_key is not None

        params: dict[str, str | float | int] = {
            "lat": coords.lat,
            "lon": coords.lon,
            "appid": self.api_key,
            "units": "metric",  # 摂氏温度
            "lang": "ja",  # 日本語の天気説明
            "cnt": 40,  # 5日間分（3時間ごと×8回×5日）
        }

        async with aiohttp.ClientSession() as session:
            # 5日間予報を取得
            async with session.get(self.base_url + "/forecast", params=params) as response:
                if response.status != 200:
                    raise WeatherAPIError(f"Weather API error: {response.status}")

                data = await response.json()

            # 日付ごとの天気データを集計
            daily_data: dict[date, list[dict[str, Any]]] = {}
            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                forecast_date = dt.date()

                # 期間内のデータのみ処理
                if start_date <= forecast_date <= end_date:
                    if forecast_date not in daily_data:
                        daily_data[forecast_date] = []
                    daily_data[forecast_date].append(item)

            # 日ごとのサマリーを作成
            forecasts = []
            for forecast_date, items in sorted(daily_data.items()):
                # その日の最高・最低気温を計算
                temps = [item["main"]["temp"] for item in items]
                feels_like_temps = [item["main"]["feels_like"] for item in items]
                humidities = [item["main"]["humidity"] for item in items]
                wind_speeds = [item["wind"]["speed"] for item in items]

                # 降水確率（popは0-1の値）
                rain_probs = [item.get("pop", 0) * 100 for item in items]

                # 最も頻出する天気条件を選択
                weather_conditions = {}
                for item in items:
                    condition = item["weather"][0]["main"]
                    description = item["weather"][0]["description"]
                    weather_conditions[condition] = description

                most_common_condition = max(
                    weather_conditions.keys(),
                    key=lambda x: sum(1 for item in items if item["weather"][0]["main"] == x),
                )

                forecasts.append(
                    WeatherData(
                        date=forecast_date,
                        temperature=sum(temps) / len(temps),
                        feels_like=sum(feels_like_temps) / len(feels_like_temps),
                        temp_min=min(temps),
                        temp_max=max(temps),
                        humidity=int(sum(humidities) / len(humidities)),
                        rain_probability=max(rain_probs) if rain_probs else 0,
                        weather_condition=most_common_condition,
                        weather_description=weather_conditions[most_common_condition],
                        wind_speed=sum(wind_speeds) / len(wind_speeds),
                    )
                )

            # もし予報期間外の場合は、現在の天気を使用
            if not forecasts and (date.today() <= start_date <= date.today() + timedelta(days=1)):
                current = await self._get_current_weather(coords)
                if current:
                    forecasts.append(current)

            return forecasts

    async def _get_current_weather(self, coords: Coordinates) -> WeatherData | None:
        """現在の天気を取得（予報が取得できない場合のフォールバック）."""
        # この時点でapi_keyは必ず存在する（get_weather_summaryでチェック済み）
        assert self.api_key is not None

        params: dict[str, str | float] = {
            "lat": coords.lat,
            "lon": coords.lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ja",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url + "/weather", params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return WeatherData(
                    date=date.today(),
                    temperature=data["main"]["temp"],
                    feels_like=data["main"]["feels_like"],
                    temp_min=data["main"]["temp_min"],
                    temp_max=data["main"]["temp_max"],
                    humidity=data["main"]["humidity"],
                    rain_probability=0,  # 現在の天気には降水確率がない
                    weather_condition=data["weather"][0]["main"],
                    weather_description=data["weather"][0]["description"],
                    wind_speed=data["wind"]["speed"],
                )

    def _create_summary(
        self, location: str, start_date: date, end_date: date, forecasts: list[WeatherData]
    ) -> WeatherSummary:
        """天気データからサマリーを作成."""
        if not forecasts:
            # データがない場合のデフォルト
            return WeatherSummary(
                location=location,
                start_date=start_date,
                end_date=end_date,
                daily_forecasts=[],
                has_rain=False,
                min_temperature=20.0,
                max_temperature=25.0,
                avg_temperature=22.5,
                max_rain_probability=0,
                weather_conditions=["Clear"],
            )

        temperatures = [f.temperature for f in forecasts]
        rain_probabilities = [f.rain_probability for f in forecasts]
        weather_conditions = list(set(f.weather_condition for f in forecasts))

        return WeatherSummary(
            location=location,
            start_date=start_date,
            end_date=end_date,
            daily_forecasts=forecasts,
            has_rain=any(p > 30 for p in rain_probabilities),
            min_temperature=min(f.temp_min for f in forecasts),
            max_temperature=max(f.temp_max for f in forecasts),
            avg_temperature=sum(temperatures) / len(temperatures),
            max_rain_probability=max(rain_probabilities) if rain_probabilities else 0,
            weather_conditions=weather_conditions,
        )

    def _get_from_cache(self, key: str) -> WeatherSummary | None:
        """キャッシュから取得."""
        if key in self._cache:
            summary, cached_at = self._cache[key]
            if datetime.now() - cached_at < self._cache_duration:
                return summary
            else:
                del self._cache[key]
        return None

    def _save_to_cache(self, key: str, summary: WeatherSummary) -> None:
        """キャッシュに保存."""
        self._cache[key] = (summary, datetime.now())
        # キャッシュサイズ制限（最大100件）
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]


# テスト用の関数
async def test_weather_service() -> None:
    """Weather Serviceのテスト."""
    service = WeatherService()
    try:
        summary = await service.get_weather_summary(
            "Tokyo", date.today(), date.today() + timedelta(days=3)
        )
        print(f"Location: {summary.location}")
        print(f"Period: {summary.start_date} to {summary.end_date}")
        print(f"Has rain: {summary.has_rain}")
        print(f"Temperature range: {summary.min_temperature}°C - {summary.max_temperature}°C")
        print(f"Max rain probability: {summary.max_rain_probability}%")
        print(f"Weather conditions: {', '.join(summary.weather_conditions)}")
        print("\nDaily forecasts:")
        for forecast in summary.daily_forecasts:
            print(
                f"  {forecast.date}: {forecast.weather_description} "
                f"({forecast.temp_min:.1f}°C - {forecast.temp_max:.1f}°C), "
                f"Rain: {forecast.rain_probability:.0f}%"
            )
    except WeatherAPIError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_weather_service())
