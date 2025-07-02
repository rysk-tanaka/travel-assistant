"""
Unit tests for models module.

外部依存のないモデルクラスのテストを実施します。
"""

from datetime import date, datetime, timedelta
from uuid import UUID

import pytest

from src.models import (
    AccommodationInfo,
    ChecklistItem,
    FlightInfo,
    GitHubSyncError,
    Meeting,
    TemplateNotFoundError,
    TransportSegment,
    TravelAssistantError,
    TripChecklist,
    TripItinerary,
    TripRequest,
    WeatherAPIError,
)


# ChecklistItem Tests
def test_create_basic_item():
    """基本的なアイテムの作成."""
    item = ChecklistItem(
        name="パスポート",
        category="移動関連",
    )

    assert item.name == "パスポート"
    assert item.category == "移動関連"
    assert item.checked is False
    assert item.auto_added is False
    assert item.reason is None
    assert isinstance(item.item_id, str)
    assert UUID(item.item_id)  # Valid UUID


def test_create_auto_added_item():
    """自動追加アイテムの作成."""
    item = ChecklistItem(
        name="防寒着",
        category="服装・身だしなみ",
        auto_added=True,
        reason="北海道の冬は寒いため",
    )

    assert item.auto_added is True
    assert item.reason == "北海道の冬は寒いため"


def test_item_string_representation():
    """アイテムの文字列表現."""
    item_unchecked = ChecklistItem(name="歯ブラシ", category="生活用品")
    assert str(item_unchecked) == "⬜ 歯ブラシ"

    item_checked = ChecklistItem(name="歯ブラシ", category="生活用品", checked=True)
    assert str(item_checked) == "☑️ 歯ブラシ"


def test_item_with_custom_id():
    """カスタムIDを持つアイテムの作成."""
    custom_id = "custom-item-123"
    item = ChecklistItem(
        name="テスト項目",
        category="生活用品",
        item_id=custom_id,
    )
    assert item.item_id == custom_id


# TripRequest Tests
def test_create_basic_request():
    """基本的なリクエストの作成."""
    request = TripRequest(
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="user123",
    )

    assert request.destination == "札幌"
    assert request.start_date == date(2025, 6, 28)
    assert request.end_date == date(2025, 6, 30)
    assert request.purpose == "business"
    assert request.user_id == "user123"
    assert request.transport_method is None
    assert request.accommodation is None


def test_create_full_request():
    """全項目を指定したリクエストの作成."""
    request = TripRequest(
        destination="大阪",
        start_date=date(2025, 7, 15),
        end_date=date(2025, 7, 18),
        purpose="leisure",
        transport_method="train",
        accommodation="大阪ホテル",
        user_id="user456",
    )

    assert request.transport_method == "train"
    assert request.accommodation == "大阪ホテル"


def test_computed_duration():
    """宿泊日数の計算."""
    request = TripRequest(
        destination="東京",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="user123",
    )

    assert request.duration == 2  # 2泊3日


def test_computed_trip_id():
    """旅行IDの生成."""
    request = TripRequest(
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="user123",
    )

    assert request.trip_id == "20250628-札幌-business"


def test_invalid_dates():
    """無効な日付（終了日が開始日より前）のバリデーション."""
    with pytest.raises(ValueError, match="終了日は開始日より後である必要があります"):
        TripRequest(
            destination="札幌",
            start_date=date(2025, 6, 30),
            end_date=date(2025, 6, 28),  # 開始日より前
            purpose="business",
            user_id="user123",
        )


# TripChecklist Tests
@pytest.fixture
def sample_checklist() -> TripChecklist:
    """テスト用チェックリストを生成."""
    items = [
        ChecklistItem(name="パスポート", category="移動関連"),
        ChecklistItem(name="充電器", category="生活用品"),
        ChecklistItem(name="名刺", category="仕事関連", checked=True),
        ChecklistItem(name="ノートPC", category="仕事関連"),
        ChecklistItem(
            name="防寒着",
            category="服装・身だしなみ",
            auto_added=True,
            reason="北海道の冬のため",
        ),
    ]

    return TripChecklist(
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        items=items,
        user_id="user123",
        template_used="sapporo_business",
    )


def test_create_checklist(sample_checklist: TripChecklist):
    """基本的なチェックリストの作成."""
    assert sample_checklist.destination == "札幌"
    assert len(sample_checklist.items) == 5
    assert sample_checklist.status == "planning"
    assert isinstance(sample_checklist.id, str)
    assert UUID(sample_checklist.id)  # Valid UUID


def test_items_by_category(sample_checklist: TripChecklist):
    """カテゴリ別アイテムの整理."""
    by_category = sample_checklist.items_by_category

    assert len(by_category) == 4  # カテゴリ数
    assert len(by_category["仕事関連"]) == 2
    assert len(by_category["移動関連"]) == 1
    assert len(by_category["生活用品"]) == 1
    assert len(by_category["服装・身だしなみ"]) == 1


def test_completion_percentage(sample_checklist: TripChecklist):
    """完了率の計算."""
    # 初期状態: 1/5が完了
    assert sample_checklist.completion_percentage == 20.0

    # もう1つチェック
    sample_checklist.items[0].checked = True
    assert sample_checklist.completion_percentage == 40.0


def test_completed_and_total_count(sample_checklist: TripChecklist):
    """完了済み・総数のカウント."""
    assert sample_checklist.completed_count == 1
    assert sample_checklist.total_count == 5


def test_pending_items(sample_checklist: TripChecklist):
    """未完了アイテムのリスト."""
    pending = sample_checklist.pending_items
    assert len(pending) == 4
    assert all(not item.checked for item in pending)


def test_toggle_item(sample_checklist: TripChecklist):
    """アイテムのチェック状態切り替え."""
    item_id = sample_checklist.items[0].item_id

    # False -> True
    result = sample_checklist.toggle_item(item_id)
    assert result is True
    assert sample_checklist.items[0].checked is True

    # True -> False
    result = sample_checklist.toggle_item(item_id)
    assert result is False
    assert sample_checklist.items[0].checked is False


def test_toggle_nonexistent_item(sample_checklist: TripChecklist):
    """存在しないアイテムのトグル."""
    with pytest.raises(ValueError, match="Item with id invalid-id not found"):
        sample_checklist.toggle_item("invalid-id")


def test_add_item(sample_checklist: TripChecklist):
    """アイテムの追加."""
    new_item = ChecklistItem(name="傘", category="天気対応")
    initial_count = len(sample_checklist.items)

    sample_checklist.add_item(new_item)

    assert len(sample_checklist.items) == initial_count + 1
    assert sample_checklist.items[-1].name == "傘"


def test_remove_item(sample_checklist: TripChecklist):
    """アイテムの削除."""
    item_id = sample_checklist.items[0].item_id
    initial_count = len(sample_checklist.items)

    sample_checklist.remove_item(item_id)

    assert len(sample_checklist.items) == initial_count - 1
    assert all(item.item_id != item_id for item in sample_checklist.items)


def test_to_markdown(sample_checklist: TripChecklist):
    """Markdown形式への変換."""
    markdown = sample_checklist.to_markdown()

    # 基本情報の確認
    assert "# 札幌旅行チェックリスト" in markdown
    assert "**期間**: 2025-06-28 ～ 2025-06-30" in markdown
    assert "**目的**: business" in markdown
    assert "**進捗**: 20.0% (1/5)" in markdown

    # チェックリスト項目の確認
    assert "## 移動関連" in markdown
    assert "- [ ] パスポート" in markdown
    assert "- [x] 名刺" in markdown

    # 自動追加項目の理由表示
    assert "- [ ] 防寒着" in markdown
    assert "  - ⭐ 北海道の冬のため" in markdown


def test_empty_checklist():
    """空のチェックリストの動作."""
    checklist = TripChecklist(
        destination="東京",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 2),
        purpose="leisure",
        items=[],
        user_id="user789",
    )

    assert checklist.completion_percentage == 0.0
    assert checklist.completed_count == 0
    assert checklist.total_count == 0
    assert len(checklist.pending_items) == 0
    assert len(checklist.items_by_category) == 0


# Exception Tests
def test_base_exception():
    """基本例外クラス."""
    error = TravelAssistantError("エラーが発生しました")
    assert str(error) == "エラーが発生しました"
    assert isinstance(error, Exception)


def test_template_not_found_error():
    """テンプレート未発見例外."""
    error = TemplateNotFoundError("テンプレートが見つかりません: business.md")
    assert "business.md" in str(error)
    assert isinstance(error, TravelAssistantError)


def test_weather_api_error():
    """天気API例外."""
    error = WeatherAPIError("天気情報の取得に失敗しました")
    assert "天気情報" in str(error)
    assert isinstance(error, TravelAssistantError)


def test_github_sync_error():
    """GitHub同期例外."""
    error = GitHubSyncError("GitHubへの保存に失敗しました")
    assert "GitHub" in str(error)
    assert isinstance(error, TravelAssistantError)


# Additional tests for uncovered functionality
def test_adjust_for_duration_change_extend(sample_checklist: TripChecklist):
    """期間延長時のチェックリスト調整."""
    # 2泊から4泊に延長
    adjustments = sample_checklist.adjust_for_duration_change(2, 4)

    assert len(adjustments) > 0
    assert any("洗濯用洗剤" in adj for adj in adjustments)

    # 洗濯用洗剤が追加されているか確認
    laundry_items = [item for item in sample_checklist.items if "洗濯" in item.name]
    assert len(laundry_items) > 0
    assert laundry_items[0].auto_added is True


def test_adjust_for_duration_change_extend_long(sample_checklist: TripChecklist):
    """長期滞在への調整."""
    # 2泊から5泊に延長
    adjustments = sample_checklist.adjust_for_duration_change(2, 5)

    assert len(adjustments) > 0
    assert any("長期滞在用" in adj for adj in adjustments)

    # 長期滞在用アイテムが追加されているか確認
    long_stay_items = [
        item
        for item in sample_checklist.items
        if item.auto_added and "長期滞在" in (item.reason or "")
    ]
    assert len(long_stay_items) >= 2  # 爪切りと予備充電ケーブル


def test_adjust_for_duration_change_shorten(sample_checklist: TripChecklist):
    """期間短縮時のチェックリスト調整."""
    # まず洗濯用品を追加
    laundry_item = ChecklistItem(
        name="洗濯用洗剤（小分け）",
        category="生活用品",
        auto_added=True,
        reason="3泊の長期滞在のため",
    )
    sample_checklist.add_item(laundry_item)
    initial_count = len(sample_checklist.items)

    # 3泊から2泊に短縮
    adjustments = sample_checklist.adjust_for_duration_change(3, 2)

    assert len(adjustments) > 0
    assert any("削除しました" in adj for adj in adjustments)
    assert len(sample_checklist.items) < initial_count


def test_get_item(sample_checklist: TripChecklist):
    """アイテムの取得."""
    # 名前でアイテムを検索する機能があるか確認
    # 存在するアイテムの取得
    item = None
    for i in sample_checklist.items:
        if i.name == "パスポート":
            item = i
            break

    assert item is not None
    assert item.name == "パスポート"


# Test different trip purposes
def test_trip_request_with_different_purposes():
    """異なる目的の旅行リクエスト."""
    # business purpose
    business_trip = TripRequest(
        destination="東京",
        start_date=date(2025, 7, 10),
        end_date=date(2025, 7, 12),
        purpose="business",
        user_id="user123",
    )
    assert business_trip.purpose == "business"

    # leisure purpose
    leisure_trip = TripRequest(
        destination="京都",
        start_date=date(2025, 8, 10),
        end_date=date(2025, 8, 15),
        purpose="leisure",
        user_id="user123",
    )
    assert leisure_trip.purpose == "leisure"


# Test different transport methods
def test_trip_request_with_different_transport():
    """異なる交通手段の旅行リクエスト."""
    transport_methods = ["airplane", "train", "car", "bus", "other"]

    for method in transport_methods:
        trip = TripRequest(
            destination="名古屋",
            start_date=date(2025, 7, 20),
            end_date=date(2025, 7, 22),
            purpose="business",
            transport_method=method,
            user_id="user123",
        )
        assert trip.transport_method == method


# Flight-related model tests
def test_flight_info():
    """FlightInfo モデルのテスト."""
    flight = FlightInfo(
        flight_number="ANA123",
        airline="全日空",
        departure_airport="HND",
        arrival_airport="CTS",
        scheduled_departure=datetime(2025, 6, 28, 9, 0),
        scheduled_arrival=datetime(2025, 6, 28, 10, 35),
        terminal="第2",
        gate="66",
        seat="12A",
        confirmation_code="ABC123",
    )

    assert flight.flight_number == "ANA123"
    assert flight.airline == "全日空"
    assert flight.departure_airport == "HND"
    assert flight.arrival_airport == "CTS"
    assert flight.status == "scheduled"

    # Computed fields
    assert flight.flight_duration == timedelta(hours=1, minutes=35)
    assert flight.is_early_morning is False

    # Early morning flight
    early_flight = FlightInfo(
        flight_number="JAL456",
        airline="日本航空",
        departure_airport="HND",
        arrival_airport="KIX",
        scheduled_departure=datetime(2025, 6, 28, 6, 30),
        scheduled_arrival=datetime(2025, 6, 28, 8, 0),
    )
    assert early_flight.is_early_morning is True


def test_accommodation_info():
    """AccommodationInfo モデルのテスト."""
    hotel = AccommodationInfo(
        name="札幌グランドホテル",
        type="hotel",
        check_in=datetime(2025, 6, 28, 15, 0),
        check_out=datetime(2025, 6, 30, 11, 0),
        address="札幌市中央区北1条西4丁目",
        phone="011-261-3311",
        confirmation_code="HTL789",
        notes="朝食付きプラン",
    )

    assert hotel.name == "札幌グランドホテル"
    assert hotel.type == "hotel"
    assert hotel.nights == 2


def test_transport_segment():
    """TransportSegment モデルのテスト."""
    train = TransportSegment(
        type="train",
        provider="JR北海道",
        from_location="新千歳空港駅",
        to_location="札幌駅",
        departure_time=datetime(2025, 6, 28, 11, 0),
        arrival_time=datetime(2025, 6, 28, 11, 37),
        reservation_required=False,
    )

    assert train.type == "train"
    assert train.provider == "JR北海道"
    assert train.from_location == "新千歳空港駅"
    assert train.to_location == "札幌駅"
    assert train.reservation_required is False


def test_meeting():
    """Meeting モデルのテスト."""
    meeting = Meeting(
        title="プロジェクト打ち合わせ",
        location="札幌オフィス会議室A",
        start_time=datetime(2025, 6, 29, 10, 0),
        end_time=datetime(2025, 6, 29, 12, 0),
        attendees=["山田太郎", "佐藤花子", "鈴木一郎"],
        notes="資料は事前に共有済み",
    )

    assert meeting.title == "プロジェクト打ち合わせ"
    assert meeting.location == "札幌オフィス会議室A"
    assert len(meeting.attendees) == 3
    assert "山田太郎" in meeting.attendees


def test_trip_itinerary():
    """TripItinerary モデルのテスト."""
    flight = FlightInfo(
        flight_number="ANA123",
        airline="全日空",
        departure_airport="HND",
        arrival_airport="CTS",
        scheduled_departure=datetime(2025, 6, 28, 9, 0),
        scheduled_arrival=datetime(2025, 6, 28, 10, 35),
    )

    hotel = AccommodationInfo(
        name="札幌グランドホテル",
        type="hotel",
        check_in=datetime(2025, 6, 28, 15, 0),
        check_out=datetime(2025, 6, 30, 11, 0),
        address="札幌市中央区北1条西4丁目",
    )

    itinerary = TripItinerary(
        trip_id="20250628-札幌-business",
        flights=[flight],
        accommodations=[hotel],
    )

    assert itinerary.trip_id == "20250628-札幌-business"
    assert len(itinerary.flights) == 1
    assert len(itinerary.accommodations) == 1

    # Timeline events
    timeline = itinerary.timeline_events
    assert len(timeline) == 4  # 出発、到着、チェックイン、チェックアウト

    # Events should be sorted by time
    event_times = [event[0] for event in timeline]
    assert event_times == sorted(event_times)

    # Check event types
    assert timeline[0][1] == "flight_departure"
    assert timeline[1][1] == "flight_arrival"
    assert timeline[2][1] == "hotel_checkin"
    assert timeline[3][1] == "hotel_checkout"


# Additional model field tests
def test_checklist_with_custom_id():
    """カスタムIDを持つチェックリストの作成."""
    custom_id = "custom-checklist-001"
    checklist = TripChecklist(
        id=custom_id,
        destination="東京",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 2),
        purpose="business",
        user_id="user123",
    )
    assert checklist.id == custom_id


def test_checklist_update_timestamp():
    """チェックリストの更新タイムスタンプ."""
    checklist = TripChecklist(
        destination="東京",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 2),
        purpose="business",
        user_id="user123",
    )

    initial_updated = checklist.updated_at

    # Add item updates timestamp
    item = ChecklistItem(name="テストアイテム", category="生活用品")
    checklist.add_item(item)

    assert checklist.updated_at > initial_updated
