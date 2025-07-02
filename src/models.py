"""
Type definitions for TravelAssistant.

このファイルには、プロジェクト全体で使用される型定義を集約します。
Python 3.12+の新しい型構文を使用します。
"""

from datetime import date, datetime, timedelta
from typing import Any, Literal, TypedDict
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
type FlightStatus = Literal["scheduled", "delayed", "cancelled", "arrived"]
type AccommodationType = Literal["hotel", "ryokan", "airbnb", "friends", "other"]


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
    def validate_dates(cls, v: date, info: Any) -> date:
        """終了日が開始日より後であることを検証."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> int:
        """宿泊日数を計算."""
        return (self.end_date - self.start_date).days

    @computed_field  # type: ignore[prop-decorator]
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def items_by_category(self) -> dict[ItemCategory, list[ChecklistItem]]:
        """カテゴリ別にアイテムを整理."""
        result: dict[ItemCategory, list[ChecklistItem]] = {}
        for item in self.items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result

    @computed_field  # type: ignore[prop-decorator]
    @property
    def completion_percentage(self) -> float:
        """完了率を計算."""
        if not self.items:
            return 0.0
        checked_count = sum(1 for item in self.items if item.checked)
        return (checked_count / len(self.items)) * 100

    @computed_field  # type: ignore[prop-decorator]
    @property
    def completed_count(self) -> int:
        """完了済みアイテム数."""
        return sum(1 for item in self.items if item.checked)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_count(self) -> int:
        """全アイテム数."""
        return len(self.items)

    @computed_field  # type: ignore[prop-decorator]
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

    def adjust_for_duration_change(self, old_duration: int, new_duration: int) -> list[str]:
        """期間変更に応じてチェックリストを調整.

        Args:
            old_duration: 変更前の宿泊日数
            new_duration: 変更後の宿泊日数

        Returns:
            実行された調整のリスト
        """
        adjustments = []

        if new_duration > old_duration:
            # 期間が延長された場合
            new_duration - old_duration

            # 着替えの追加
            clothing_items = [
                item
                for item in self.items
                if item.category == "服装・身だしなみ" and "着替え" in item.name
            ]
            if clothing_items:
                adjustments.append(
                    f"着替えを{old_duration}泊分から{new_duration}泊分に増やしました"
                )
                # TODO: 実際の数量調整

            # 長期滞在用アイテムの追加
            if new_duration >= 3 and old_duration < 3:
                # 洗濯用品の追加
                laundry_item = ChecklistItem(
                    name="洗濯用洗剤（小分け）",
                    category="生活用品",
                    auto_added=True,
                    reason=f"{new_duration}泊の長期滞在のため",
                )
                self.add_item(laundry_item)
                adjustments.append("洗濯用洗剤を追加しました（3泊以上）")

            if new_duration >= 5 and old_duration < 5:
                # さらに長期滞在用
                extra_items = [
                    ChecklistItem(
                        name="爪切り",
                        category="生活用品",
                        auto_added=True,
                        reason=f"{new_duration}泊の長期滞在のため",
                    ),
                    ChecklistItem(
                        name="予備の充電ケーブル",
                        category="生活用品",
                        auto_added=True,
                        reason=f"{new_duration}泊の長期滞在のため",
                    ),
                ]
                for item in extra_items:
                    self.add_item(item)
                adjustments.append("長期滞在用アイテムを追加しました（5泊以上）")

        elif new_duration < old_duration:
            # 期間が短縮された場合
            # 長期滞在用アイテムの削除を検討
            if new_duration < 3 and old_duration >= 3:
                # 洗濯用品を削除候補に
                laundry_items = [
                    item for item in self.items if item.auto_added and "洗濯" in item.name
                ]
                for item in laundry_items:
                    self.remove_item(item.item_id)
                    adjustments.append(f"{item.name}を削除しました（短期滞在）")

            # 着替えの削減提案
            adjustments.append(
                f"着替えを{old_duration}泊分から{new_duration}泊分に減らすことを検討してください"
            )

        return adjustments

    def to_markdown(self) -> str:
        """Markdown形式でチェックリストを出力."""
        progress = f"{self.completion_percentage:.1f}%"
        lines = [
            f"# {self.destination}旅行チェックリスト",
            f"**期間**: {self.start_date} ～ {self.end_date}",
            f"**目的**: {self.purpose}",
            f"**進捗**: {progress} ({self.completed_count}/{self.total_count})",
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


# Itinerary-related Models
class FlightInfo(BaseModel):
    """フライト情報."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="フライトID")
    flight_number: str = Field(..., description="便名")
    airline: str = Field(..., description="航空会社")
    departure_airport: str = Field(..., description="出発空港コード")
    arrival_airport: str = Field(..., description="到着空港コード")
    scheduled_departure: datetime = Field(..., description="予定出発時刻")
    scheduled_arrival: datetime = Field(..., description="予定到着時刻")
    actual_departure: datetime | None = Field(default=None, description="実際の出発時刻")
    actual_arrival: datetime | None = Field(default=None, description="実際の到着時刻")
    terminal: str | None = Field(default=None, description="ターミナル")
    gate: str | None = Field(default=None, description="搭乗ゲート")
    seat: str | None = Field(default=None, description="座席番号")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")
    status: FlightStatus = Field(default="scheduled", description="フライト状態")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def flight_duration(self) -> timedelta:
        """フライト時間を計算."""
        return self.scheduled_arrival - self.scheduled_departure

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_early_morning(self) -> bool:
        """早朝便かどうか."""
        return self.scheduled_departure.hour < 8


class AccommodationInfo(BaseModel):
    """宿泊情報."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="宿泊ID")
    name: str = Field(..., description="宿泊施設名")
    type: AccommodationType = Field(..., description="宿泊タイプ")
    check_in: datetime = Field(..., description="チェックイン時刻")
    check_out: datetime = Field(..., description="チェックアウト時刻")
    address: str = Field(..., description="住所")
    phone: str | None = Field(default=None, description="電話番号")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")
    notes: str | None = Field(default=None, description="備考")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nights(self) -> int:
        """宿泊日数."""
        return (self.check_out.date() - self.check_in.date()).days


class TransportSegment(BaseModel):
    """移動区間情報."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="移動区間ID")
    type: TransportMethod = Field(..., description="交通手段")
    provider: str | None = Field(default=None, description="運行会社")
    from_location: str = Field(..., description="出発地")
    to_location: str = Field(..., description="到着地")
    departure_time: datetime = Field(..., description="出発時刻")
    arrival_time: datetime = Field(..., description="到着時刻")
    reservation_required: bool = Field(default=False, description="予約必須かどうか")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")


class Meeting(BaseModel):
    """会議・イベント情報."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="会議ID")
    title: str = Field(..., description="タイトル")
    location: str = Field(..., description="場所")
    start_time: datetime = Field(..., description="開始時刻")
    end_time: datetime = Field(..., description="終了時刻")
    attendees: list[str] = Field(default_factory=list, description="参加者")
    notes: str | None = Field(default=None, description="備考")


class TripItinerary(BaseModel):
    """旅行行程."""

    trip_id: str = Field(..., description="旅行ID")
    flights: list[FlightInfo] = Field(default_factory=list, description="フライト情報")
    accommodations: list[AccommodationInfo] = Field(default_factory=list, description="宿泊情報")
    transport_segments: list[TransportSegment] = Field(
        default_factory=list, description="その他の移動"
    )
    meetings: list[Meeting] = Field(default_factory=list, description="会議・イベント")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def timeline_events(self) -> list[tuple[datetime, str, str]]:
        """時系列でイベントを整理."""
        events = []

        # フライト
        for flight in self.flights:
            events.append(
                (flight.scheduled_departure, "flight_departure", f"✈️ {flight.flight_number} 出発")
            )
            events.append(
                (flight.scheduled_arrival, "flight_arrival", f"🛬 {flight.arrival_airport} 到着")
            )

        # 宿泊
        for hotel in self.accommodations:
            events.append((hotel.check_in, "hotel_checkin", f"🏨 {hotel.name} チェックイン"))
            events.append((hotel.check_out, "hotel_checkout", f"🏨 {hotel.name} チェックアウト"))

        # その他の移動
        for transport in self.transport_segments:
            events.append(
                (
                    transport.departure_time,
                    "transport",
                    f"🚃 {transport.from_location} → {transport.to_location}",
                )
            )

        # 会議
        for meeting in self.meetings:
            events.append((meeting.start_time, "meeting", f"📅 {meeting.title}"))

        # 時刻順にソート
        return sorted(events, key=lambda x: x[0])

    def to_markdown(self) -> str:
        """旅行行程をMarkdown形式で出力."""
        lines = ["# 旅行行程", ""]

        # タイムライン
        self._add_timeline_section(lines)

        # フライト情報詳細
        self._add_flights_section(lines)

        # 宿泊情報詳細
        self._add_accommodations_section(lines)

        # 会議・イベント情報詳細
        self._add_meetings_section(lines)

        return "\n".join(lines)

    def _add_timeline_section(self, lines: list[str]) -> None:
        """タイムラインセクションを追加."""
        timeline_events = self.timeline_events
        if not timeline_events:
            return

        lines.append("## 📅 タイムライン")
        lines.append("")

        current_date = None
        for event_time, _event_type, event_desc in timeline_events:
            event_date = event_time.date()

            # 日付が変わったら見出しを追加
            if event_date != current_date:
                current_date = event_date
                lines.append(f"### {event_date.strftime('%Y年%m月%d日 (%a)')}")
                lines.append("")

            time_str = event_time.strftime("%H:%M")
            lines.append(f"- **{time_str}** {event_desc}")

        lines.append("")

    def _add_flights_section(self, lines: list[str]) -> None:
        """フライト情報セクションを追加."""
        if not self.flights:
            return

        lines.append("## ✈️ フライト情報")
        lines.append("")

        for flight in self.flights:
            lines.append(f"### {flight.flight_number} ({flight.airline})")
            lines.append(f"- 区間: {flight.departure_airport} → {flight.arrival_airport}")
            lines.append(f"- 出発: {flight.scheduled_departure.strftime('%Y/%m/%d %H:%M')}")
            lines.append(f"- 到着: {flight.scheduled_arrival.strftime('%Y/%m/%d %H:%M')}")
            if flight.confirmation_code:
                lines.append(f"- 予約番号: {flight.confirmation_code}")
            if flight.seat:
                lines.append(f"- 座席: {flight.seat}")
            lines.append("")

    def _add_accommodations_section(self, lines: list[str]) -> None:
        """宿泊情報セクションを追加."""
        if not self.accommodations:
            return

        lines.append("## 🏨 宿泊情報")
        lines.append("")

        for hotel in self.accommodations:
            lines.append(f"### {hotel.name}")
            lines.append(f"- タイプ: {hotel.type}")
            lines.append(f"- チェックイン: {hotel.check_in.strftime('%Y/%m/%d %H:%M')}")
            lines.append(f"- チェックアウト: {hotel.check_out.strftime('%Y/%m/%d %H:%M')}")
            lines.append(f"- 住所: {hotel.address}")
            if hotel.phone:
                lines.append(f"- 電話: {hotel.phone}")
            if hotel.confirmation_code:
                lines.append(f"- 予約番号: {hotel.confirmation_code}")
            lines.append("")

    def _add_meetings_section(self, lines: list[str]) -> None:
        """会議・イベント情報セクションを追加."""
        if not self.meetings:
            return

        lines.append("## 📅 会議・イベント")
        lines.append("")

        for meeting in self.meetings:
            lines.append(f"### {meeting.title}")
            lines.append(f"- 場所: {meeting.location}")
            start_str = meeting.start_time.strftime("%Y/%m/%d %H:%M")
            end_str = meeting.end_time.strftime("%H:%M")
            lines.append(f"- 時間: {start_str} - {end_str}")
            if meeting.attendees:
                lines.append(f"- 参加者: {', '.join(meeting.attendees)}")
            if meeting.notes:
                lines.append(f"- 備考: {meeting.notes}")
            lines.append("")
