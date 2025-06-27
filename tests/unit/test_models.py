"""
Unit tests for models module.

外部依存のないモデルクラスのテストを実施します。
"""

from datetime import date
from uuid import UUID

import pytest
from freezegun import freeze_time

from src.models import (
    ChecklistItem,
    GitHubSyncError,
    TemplateNotFoundError,
    TravelAssistantError,
    TripChecklist,
    TripRequest,
    WeatherAPIError,
)


class TestChecklistItem:
    """ChecklistItemのテスト."""

    def test_create_basic_item(self):
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

    def test_create_auto_added_item(self):
        """自動追加アイテムの作成."""
        item = ChecklistItem(
            name="防寒着",
            category="服装・身だしなみ",
            auto_added=True,
            reason="北海道の冬は寒いため",
        )

        assert item.auto_added is True
        assert item.reason == "北海道の冬は寒いため"

    def test_item_string_representation(self):
        """アイテムの文字列表現."""
        item_unchecked = ChecklistItem(name="歯ブラシ", category="生活用品")
        assert str(item_unchecked) == "⬜ 歯ブラシ"

        item_checked = ChecklistItem(name="歯ブラシ", category="生活用品", checked=True)
        assert str(item_checked) == "☑️ 歯ブラシ"

    def test_item_with_custom_id(self):
        """カスタムIDを持つアイテムの作成."""
        custom_id = "custom-item-123"
        item = ChecklistItem(
            name="テスト項目",
            category="生活用品",
            item_id=custom_id,
        )
        assert item.item_id == custom_id


class TestTripRequest:
    """TripRequestのテスト."""

    def test_create_basic_request(self):
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

    def test_create_full_request(self):
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

    def test_computed_duration(self):
        """宿泊日数の計算."""
        request = TripRequest(
            destination="東京",
            start_date=date(2025, 6, 28),
            end_date=date(2025, 6, 30),
            purpose="business",
            user_id="user123",
        )

        assert request.duration == 2  # 2泊3日

    def test_computed_trip_id(self):
        """旅行IDの生成."""
        request = TripRequest(
            destination="札幌",
            start_date=date(2025, 6, 28),
            end_date=date(2025, 6, 30),
            purpose="business",
            user_id="user123",
        )

        assert request.trip_id == "20250628-札幌-business"

    def test_invalid_dates(self):
        """無効な日付（終了日が開始日より前）のバリデーション."""
        with pytest.raises(ValueError, match="終了日は開始日より後である必要があります"):
            TripRequest(
                destination="札幌",
                start_date=date(2025, 6, 30),
                end_date=date(2025, 6, 28),  # 開始日より前
                purpose="business",
                user_id="user123",
            )


class TestTripChecklist:
    """TripChecklistのテスト."""

    @pytest.fixture
    def sample_checklist(self) -> TripChecklist:
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

    def test_create_checklist(self, sample_checklist: TripChecklist):
        """基本的なチェックリストの作成."""
        assert sample_checklist.destination == "札幌"
        assert len(sample_checklist.items) == 5
        assert sample_checklist.status == "planning"
        assert isinstance(sample_checklist.id, str)
        assert UUID(sample_checklist.id)  # Valid UUID

    def test_items_by_category(self, sample_checklist: TripChecklist):
        """カテゴリ別アイテムの整理."""
        by_category = sample_checklist.items_by_category

        assert len(by_category) == 4  # カテゴリ数
        assert len(by_category["仕事関連"]) == 2
        assert len(by_category["移動関連"]) == 1
        assert len(by_category["生活用品"]) == 1
        assert len(by_category["服装・身だしなみ"]) == 1

    def test_completion_percentage(self, sample_checklist: TripChecklist):
        """完了率の計算."""
        # 初期状態: 1/5が完了
        assert sample_checklist.completion_percentage == 20.0

        # もう1つチェック
        sample_checklist.items[0].checked = True
        assert sample_checklist.completion_percentage == 40.0

    def test_completed_and_total_count(self, sample_checklist: TripChecklist):
        """完了済み・総数のカウント."""
        assert sample_checklist.completed_count == 1
        assert sample_checklist.total_count == 5

    def test_pending_items(self, sample_checklist: TripChecklist):
        """未完了アイテムのリスト."""
        pending = sample_checklist.pending_items
        assert len(pending) == 4
        assert all(not item.checked for item in pending)

    def test_toggle_item(self, sample_checklist: TripChecklist):
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

    def test_toggle_nonexistent_item(self, sample_checklist: TripChecklist):
        """存在しないアイテムのトグル."""
        with pytest.raises(ValueError, match="Item with id invalid-id not found"):
            sample_checklist.toggle_item("invalid-id")

    def test_add_item(self, sample_checklist: TripChecklist):
        """アイテムの追加."""
        new_item = ChecklistItem(name="傘", category="天気対応")
        initial_count = len(sample_checklist.items)

        sample_checklist.add_item(new_item)

        assert len(sample_checklist.items) == initial_count + 1
        assert sample_checklist.items[-1].name == "傘"

    def test_remove_item(self, sample_checklist: TripChecklist):
        """アイテムの削除."""
        item_id = sample_checklist.items[0].item_id
        initial_count = len(sample_checklist.items)

        sample_checklist.remove_item(item_id)

        assert len(sample_checklist.items) == initial_count - 1
        assert all(item.item_id != item_id for item in sample_checklist.items)

    @freeze_time("2025-06-27 10:00:00")
    def test_to_markdown(self, sample_checklist: TripChecklist):
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

    def test_empty_checklist(self):
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


class TestExceptions:
    """例外クラスのテスト."""

    def test_base_exception(self):
        """基本例外クラス."""
        error = TravelAssistantError("エラーが発生しました")
        assert str(error) == "エラーが発生しました"
        assert isinstance(error, Exception)

    def test_template_not_found_error(self):
        """テンプレート未発見例外."""
        error = TemplateNotFoundError("テンプレートが見つかりません: business.md")
        assert "business.md" in str(error)
        assert isinstance(error, TravelAssistantError)

    def test_weather_api_error(self):
        """天気API例外."""
        error = WeatherAPIError("天気情報の取得に失敗しました")
        assert "天気情報" in str(error)
        assert isinstance(error, TravelAssistantError)

    def test_github_sync_error(self):
        """GitHub同期例外."""
        error = GitHubSyncError("GitHubへの保存に失敗しました")
        assert "GitHub" in str(error)
        assert isinstance(error, TravelAssistantError)
