"""
Type definitions for TravelAssistant.

このファイルには、プロジェクト全体で使用される型定義を集約します。
Python 3.12+の新しい型構文を使用します。
"""

from datetime import date
from typing import Literal, TypedDict

# Type aliases using Python 3.12+ syntax
type ChecklistId = str
type UserId = str
type DestinationName = str
type TemplateType = Literal["domestic_business", "sapporo_business", "leisure_domestic"]
type TripPurpose = Literal["business", "leisure"]
type TransportMethod = Literal["airplane", "train", "car", "bus", "other"]
type ChecklistStatus = Literal["planning", "ongoing", "completed"]
type ItemCategory = Literal[
    "移動関連", "仕事関連", "服装・身だしなみ", "生活用品", "金銭関連", "天気対応", "地域特有"
]

# TypedDict definitions
class ChecklistItemDict(TypedDict):
    """チェックリストアイテムの辞書表現."""
    name: str
    category: ItemCategory
    checked: bool
    auto_added: bool
    reason: str | None


class TripInfoDict(TypedDict):
    """旅行情報の辞書表現."""
    destination: DestinationName
    start_date: str  # ISO format (YYYY-MM-DD)
    end_date: str
    purpose: TripPurpose
    transport_method: TransportMethod | None
    accommodation: str | None


class WeatherDataDict(TypedDict):
    """天気情報の辞書表現."""
    average_temperature: float
    max_temperature: float
    min_temperature: float
    rain_probability: float
    conditions: Literal["sunny", "cloudy", "rainy", "snowy"]
    forecast_date: str


class UserPreferencesDict(TypedDict):
    """ユーザー設定の辞書表現."""
    user_id: UserId
    default_transport: TransportMethod
    forgotten_items: list[str]
    preferred_accommodations: list[str]
    dietary_restrictions: list[str]


class TemplateMetadataDict(TypedDict):
    """テンプレートメタデータの辞書表現."""
    template_type: TemplateType
    template_version: str
    last_updated: str
    customizable_fields: list[str]


# Error types
class TravelAssistantError(Exception):
    """Base exception for TravelAssistant."""
    pass


class TemplateNotFoundError(TravelAssistantError):
    """テンプレートが見つからない場合の例外."""
    pass


class WeatherAPIError(TravelAssistantError):
    """天気API関連のエラー."""
    pass


class GitHubSyncError(TravelAssistantError):
    """GitHub同期関連のエラー."""
    pass