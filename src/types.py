"""
Type definitions for TravelAssistant.

このファイルには、プロジェクト全体で使用される型定義を集約します。
Python 3.12+の新しい型構文を使用します。
"""

from datetime import date, datetime
from typing import Literal, TypedDict
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

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


# Pydantic Models
class ChecklistItem(BaseModel):
    """チェックリストの個別項目."""

    name: str = Field(..., description="項目名")
    category: ItemCategory = Field(..., description="項目のカテゴリ")
    checked: bool = Field(default=False, description="チェック済みかどうか")
    auto_added: bool = Field(default=False, description="自動追加された項目かどうか")
    reason: str | None = Field(default=None, description="自動追加の理由")
    item_id: str = Field(default_factory=lambda: str(uuid4()), description="項目の一意ID")

    def __str__(self) -> str:
        """項目の文字列表現."""
        check_mark = "☑️" if self.checked else "⬜"
        return f"{check_mark} {self.name}"


class TripRequest(BaseModel):
    """旅行チェックリスト生成リクエスト."""

    destination: DestinationName = Field(..., description="目的地")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    purpose: TripPurpose = Field(..., description="旅行の目的")
    transport_method: TransportMethod | None = Field(default=None, description="交通手段")
    accommodation: str | None = Field(default=None, description="宿泊先")
    user_id: UserId = Field(..., description="ユーザーID")

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, values: dict) -> date:
        """終了日が開始日より後であることを検証."""
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")
        return v

    @computed_field
    @property
    def duration(self) -> int:
        """宿泊日数を計算."""
        return (self.end_date - self.start_date).days

    @computed_field
    @property
    def trip_id(self) -> str:
        """旅行IDを生成."""
        return f"{self.start_date.strftime('%Y%m%d')}-{self.destination}-{self.purpose}"


class TripChecklist(BaseModel):
    """完全な旅行チェックリスト."""

    id: ChecklistId = Field(default_factory=lambda: str(uuid4()), description="チェックリストID")
    destination: DestinationName = Field(..., description="目的地")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    purpose: TripPurpose = Field(..., description="旅行の目的")
    items: list[ChecklistItem] = Field(default_factory=list, description="チェックリスト項目")
    status: ChecklistStatus = Field(default="planning", description="チェックリストの状態")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")
    user_id: UserId = Field(..., description="ユーザーID")
    template_used: TemplateType | None = Field(default=None, description="使用したテンプレート")
    weather_data: WeatherDataDict | None = Field(default=None, description="天気予報データ")

    @computed_field
    @property
    def items_by_category(self) -> dict[ItemCategory, list[ChecklistItem]]:
        """カテゴリ別にアイテムを整理."""
        result: dict[ItemCategory, list[ChecklistItem]] = {}
        for item in self.items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result

    @computed_field
    @property
    def completion_percentage(self) -> float:
        """完了率を計算."""
        if not self.items:
            return 0.0
        checked_count = sum(1 for item in self.items if item.checked)
        return (checked_count / len(self.items)) * 100

    @computed_field
    @property
    def completed_count(self) -> int:
        """完了済みアイテム数."""
        return sum(1 for item in self.items if item.checked)

    @computed_field
    @property
    def total_count(self) -> int:
        """全アイテム数."""
        return len(self.items)

    @computed_field
    @property
    def pending_items(self) -> list[ChecklistItem]:
        """未完了アイテムのリスト."""
        return [item for item in self.items if not item.checked]

    def toggle_item(self, item_id: str) -> bool:
        """アイテムのチェック状態を切り替え."""
        for item in self.items:
            if item.item_id == item_id:
                item.checked = not item.checked
                self.updated_at = datetime.now()
                return item.checked
        raise ValueError(f"Item with id {item_id} not found")

    def add_item(self, item: ChecklistItem) -> None:
        """新しいアイテムを追加."""
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_item(self, item_id: str) -> None:
        """アイテムを削除."""
        self.items = [item for item in self.items if item.item_id != item_id]
        self.updated_at = datetime.now()

    def to_markdown(self) -> str:
        """Markdown形式でチェックリストを出力."""
        lines = [
            f"# {self.destination}旅行チェックリスト",
            f"**期間**: {self.start_date} ～ {self.end_date}",
            f"**目的**: {self.purpose}",
            f"**進捗**: {self.completion_percentage:.1f}% ({self.completed_count}/{self.total_count})",
            "",
        ]

        for category, items in self.items_by_category.items():
            lines.append(f"## {category}")
            for item in items:
                check = "x" if item.checked else " "
                lines.append(f"- [{check}] {item.name}")
                if item.auto_added and item.reason:
                    lines.append(f"  - ⭐ {item.reason}")
            lines.append("")

        return "\n".join(lines)
