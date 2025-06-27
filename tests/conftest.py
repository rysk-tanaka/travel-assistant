"""
pytest configuration and fixtures for TravelAssistant tests.
"""

import asyncio
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from hypothesis import settings

# Hypothesisの設定
settings.register_profile("dev", max_examples=10)
settings.register_profile("ci", max_examples=100)
settings.load_profile("dev")  # デフォルトはdev


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_checklist_dir(tmp_path: Path) -> Path:
    """一時的なチェックリストディレクトリを作成します。"""
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir(exist_ok=True)
    return checklist_dir


@pytest.fixture
def sample_trip_data() -> dict[str, Any]:
    """テスト用の旅行データを提供します。"""
    return {
        "destination": "札幌",
        "start_date": "2025-06-28",
        "end_date": "2025-06-30",
        "purpose": "business",
        "transport_method": "airplane",
        "accommodation": "札幌ビジネスホテル",
    }


@pytest.fixture
def sample_weather_data() -> dict[str, Any]:
    """テスト用の天気データを提供します。"""
    return {
        "average_temperature": 20.5,
        "max_temperature": 25.0,
        "min_temperature": 16.0,
        "rain_probability": 30.0,
        "conditions": "cloudy",
        "forecast_date": "2025-06-28",
    }
